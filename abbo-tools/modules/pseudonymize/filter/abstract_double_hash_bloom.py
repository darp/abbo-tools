import abc
import hashlib
import base64
import numpy as np
import bitarray
import ctypes
from doublehash import calc_double_hash

from abstract_filter import AbstractFilter


class AbstractDoubleHashBloomFilter(AbstractFilter):
    """
        abstract class for bloom filter which uses double hashing scheme as proposed
        by Schnell et al. ("Privacy-preserving record linkage using Bloom filters", 2009)
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, num_bits):
        super(AbstractDoubleHashBloomFilter, self).__init__()
        self._num_hash_funcs = 3
        self._num_bits = int(np.ceil(num_bits/8.0)*8)
        self._bloom = self.__init_bloomfilter()
        self._label = 0

    def __init_bloomfilter(self):
        # calculate num of bits using capacity and error rate
        bloom = bitarray.bitarray(self._num_bits, endian='little')
        bloom.setall(False)
        return bloom

    def get_libsvm_str(self):
        """
        output bloom filter as vector in LIBSVM format
        :return: str
        """
        label_str = str(self._label)
        vector_str = ' '.join(['{}:1'.format(i+1) for i in range(len(self._bloom)) if self._bloom[i]])
        return '{} {}'.format(label_str, vector_str)

    @property
    def size(self):
        return self._num_bits

    @property
    def fill_level(self):
        narray = self.to_numpy_array().flatten().reshape(-1, 1)
        return 100.0 * np.sum(narray != 0) / narray.shape[0]

    def set_label(self, label):
        valid_labels = {True: 1,
                        False: -1,
                        None: 0}
        self._label = valid_labels[label]

    def get_label(self):
        return self._label

    def reinit(self, capacity, error_rate):
        """
        reinit bloom filter with capacity and error rate instead of explicitly setting the
        number of bits. The formulas are explained in Bianci et al. (2012).

        :param capacity: capacity of bloom filter
        :param error_rate: fp probability of bloom filter
        :return: None
        """
        self._num_bits = int(np.ceil((-(capacity*np.log(error_rate))/(np.log(2)**2))/8))*8
        self._bloom = self.__init_bloomfilter()

    def set_num_hash_functions(self, num_hash_funcs):
        self._num_hash_funcs = num_hash_funcs

    def contains(self, elem):
        contains = True
        hashes = self.__get_hash_vals(elem)
        for k in hashes:
            if self._bloom[k] is False:
                contains = False
                break
        return contains

    def add(self, elem):
        """
        add string to bloom filter

        :param elem: str
        :return: list
            list of hash positions
        """
        hashes = self.__get_hash_vals(elem)
        for k in hashes:
            self._bloom[k] = True
        return hashes

    def add_to_file(self, f):
        """
        append Base64 encoded representation of Bloom filter to file

        :param f: file object
        :return: None
        """
        bloom_str = str(self._label) + '\t' + base64.b64encode(self._bloom.tobytes()) + '\n'
        f.write(bloom_str)

    def read_from_line(self, line):
        """
        converts Base64 encoded representation of bloom filter to bitarray

        :param line: label<TAB>base64encoded_bloom
        :return: None
        """
        label, bloom_str = line.strip().split('\t')
        self._label = int(label)
        self._bloom = bitarray.bitarray(endian='little')
        self._bloom.frombytes(base64.b64decode(bloom_str))

    def get_sha256(self):
        """
        returns sha256 hash as hex digests

        :return: str sha256 hash
        """
        return hashlib.sha256(self._bloom.tobytes()).hexdigest()

    def to_numpy_array(self):
        """
        converts bloom filter to numpy column vector

        :return: numpy.ndarray
        """
        return np.array(self._bloom.tolist(), dtype='int8').reshape((-1, 1))

    def fill_with_noise(self, noise_level):
        bf = self.to_numpy_array()

        # calculate number of ones to be set
        num_noise = int(np.ceil((bf.shape[0] * noise_level) / 100.0) - len(np.where(bf == 1.0)[0]))
        if num_noise > 0.0:
            zero_idcs = np.where(bf == 0.0)[0]
            noise_idcs = np.random.choice(zero_idcs, num_noise, replace=False)
            bf[noise_idcs] = 1.0
            self._bloom = bitarray.bitarray(bf[:, 0].tolist(), endian='little')

    @abc.abstractmethod
    def _hash_func1(self, elem):
        return

    @abc.abstractmethod
    def _hash_func2(self, elem):
        return

    def __get_hash_vals(self, elem):
        hash1 = ctypes.c_ulonglong(self._hash_func1(elem)).value
        hash2 = ctypes.c_ulonglong(self._hash_func2(elem)).value

        hash_list = calc_double_hash(hash1, hash2, self._num_bits, self._num_hash_funcs)
        return hash_list

    def calc_similarity(self, other, simtype=None):
        v1 = self.to_numpy_array()
        v2 = other.to_numpy_array()
        if simtype == 'simple':
            dist = np.abs(np.sum(v1) - np.sum(v2)) / float(len(v1))
        else:
            dist = 1.0 - (np.sum(v1 & v2) / float(np.sum(v1 | v2)))
        return dist

    def merge(self, other):
        self.__logical_or(other)

    def __logical_or(self, other):
        """
        bitwise OR between two bloom filters

        :param other: another bloom filter
        :return: None
        """
        b1 = self.to_numpy_array()
        b2 = other.to_numpy_array()
        bor = np.logical_or(b1, b2).astype('int8')
        self._label = max(self._label, other.get_label())
        self._bloom = bitarray.bitarray(bor[:, 0].tolist(), endian='little')

