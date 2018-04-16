import numpy as np
import ctypes
import mmh3
import base64
import simplejson as json
from abstract_filter import AbstractFilter
from doublehash import calc_double_hash


class CountMinSketchFilter(AbstractFilter):

    def __init__(self, num_bits):
        super(CountMinSketchFilter, self).__init__()
        self._num_hash_funcs = 1
        self._bits_per_sketch = num_bits
        self._filter = self.__init_filter()
        self._label = 0

    def __init_filter(self):
        return np.zeros((self._num_hash_funcs, self._bits_per_sketch), dtype='int16')

    def set_num_hash_functions(self, num_hash_funcs):
        self._num_hash_funcs = num_hash_funcs
        self._filter = self.__init_filter()

    def add(self, elem):
        """
        add string to filter

        :param elem: str
        :return: None
        """
        hashes = self.__get_hash_vals(elem)
        for i in range(len(hashes)):
            self._filter[i, hashes[i]] += 1

    def get_num_of_inserts(self, elem):
        """
        returns how many times an element has (probably)
        been added to the count min sketch

        :param elem: str
        :return: int
        """
        hashes = self.__get_hash_vals(elem)
        vals = list()
        for i in range(len(hashes)):
            vals.append(self._filter[i, hashes[i]])
        return min(vals)

    def __get_hash_vals(self, elem):
        hash1 = ctypes.c_ulonglong(self._hash_func1(elem)).value
        hash2 = ctypes.c_ulonglong(self._hash_func2(elem)).value

        hash_list = calc_double_hash(hash1, hash2, self._bits_per_sketch, self._num_hash_funcs)
        return hash_list

    def _hash_func1(self, elem):
        return mmh3.hash(json.dumps(elem, ensure_ascii=True), 0)

    def _hash_func2(self, elem):
        hash1 = self._hash_func1(elem)
        return mmh3.hash(json.dumps(elem, ensure_ascii=True), hash1)

    def get_libsvm_str(self):
        """
        output Bloomfilter as vector in LIBSVM format
        :return: str
        """
        label_str = str(self._label)
        vector = self._filter.flatten()
        vector_str = ' '.join(['{}:{}'.format(i+1, vector[i]) for i in range(len(vector)) if vector[i]])
        return '{} {}'.format(label_str, vector_str)

    def fill_with_noise(self, noise_level):
        """
        fill count min sketch with random noise values

        :param noise_level: desired fill level in percent
        :return: None
        """
        # calculate number of positions to be set
        num_noise = int(np.ceil((self._filter.flatten().shape[0] * noise_level) / 100.0) - len(np.where(self._filter.flatten() != 0.0)[0]))
        maxval = np.max(self._filter)
        if num_noise > 0.0:
            zero_idcs = np.where(self._filter == 0.0)
            noise_idcs = np.random.choice(range(len(zero_idcs[0])), num_noise, replace=False)
            m = self._filter.copy()
            val = 1
            if maxval > 1:
                val = np.random.randint(1, maxval)
            m[zero_idcs[0][noise_idcs], zero_idcs[1][noise_idcs]] = val
            self._filter = m

    def add_to_file(self, f):
        """
        append Base64 encoded representation of count min sketch to file

        :param f: file object
        :return: None
        """
        bloom_str = str(self._label) + '\t' + base64.b64encode(self._filter) + '\n'
        f.write(bloom_str)

    def read_from_line(self, line):
        """
        converts Base64 encoded representation of Count-Min sketch to numpy array

        :param line: label<TAB>base64encoded_bloom
        :return: None
        """
        label, base_string = line.strip().split('\t')
        self._label = int(label)
        dec_string = base64.decodestring(base_string)
        self._filter = np.frombuffer(dec_string, dtype=np.int16).reshape(-1, self._num_hash_funcs)
        self._bits_per_sketch = self._filter.shape[0]

    def to_numpy_array(self):
        """
        converts count-min sketch to numpy column vector

        :return: numpy.ndarray
        """
        return self._filter.flatten().reshape(-1, 1)

    @property
    def size(self):
        return self._bits_per_sketch * self._num_hash_funcs

    @property
    def fill_level(self):
        narray = self._filter.flatten().reshape(-1, 1)
        return 100.0 * np.sum(narray != 0) / narray.shape[0]

    def calc_similarity(self, other, simtype=None):
        v1 = self.to_numpy_array()
        v2 = other.to_numpy_array()
        if simtype == 'simple':
            # don't consider position of elements
            dist = 1.0 - (np.sum(np.intersect1d(v1, v2)) / max(1.0, float(np.sum(np.union1d(v1, v2)))))
        else:
            dist = 1.0 - (np.sum((v1 != 0) & (v2 != 0)) / max(1.0, float(np.sum((v1 != 0) | (v2 != 0)))))
        return dist

    def set_label(self, label):
        self._label = label

    def get_label(self):
        return self._label

    def merge(self, other):
        """
        returns elementwise maximum of both sketches

        :param other: another cm sketch
        :return: None
        """
        other = other.to_numpy_array()
        self._filter = np.maximum(self._filter, other).astype('int16')
