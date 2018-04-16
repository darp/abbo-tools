from __future__ import print_function
import sys
import numpy as np
from modules.pseudonymize.filter.bloom_factory import BloomFilter


class HardeningModule(object):

    def __init__(self):
        self.__input = None
        self.__output = None
        self.__chunk_size = 10  # merging is peformaned on chunks of data
        self.__anon_level = 1
        self.__type = 'bloom'  # set filter type (bloom or count)
        self.__noise_level = 0  # noise level in percent
        self.__merge_mode = 'train'
        self.__verbose = False

    def set_input(self, input):
        """
        input file containing pseudonymized orders and labels separated by newline characters

        :param input: name of file
        :return: None
        """
        self.__input = input

    def set_output(self, output):
        """
        output file containing anonymized orders and labels separated by newline characters

        :param output: name of file
        :return:
        """
        self.__output = output

    def set_filter_type(self, filter_type):
        if filter_type != 'count':
            filter_type = 'murmur'
        self.__type = filter_type

    def set_noise_level(self, noise_level):
        if not (0.0 <= noise_level <= 100.0):
            raise ValueError("Noise level has to be in range [0, 100].")
        self.__noise_level = noise_level

    def set_merging_level(self, anon_level):
        self.__anon_level = anon_level if self.__anon_level > 0 else 1
        while (self.__chunk_size % self.__anon_level) != 0:
            self.__chunk_size += 1

    def set_merging_mode(self, merge_mode):
        """
        set merging mode depending whether merging
        is applied on training or test set. In particular,
        only merge orders with the same label when merging
        training data. Ignore labels, in case a test set is
        merged.

        :param merge_mode: str
        :return: None
        """
        self.__merge_mode = merge_mode

    def set_chunk_size(self, chunk_size):
        """
        data is processed in chunks of 'chunk_size' bloom filters

        :param chunk_size: int
        :return: None
        """
        multiple = chunk_size
        while (multiple % self.__anon_level) != 0:
            multiple += 1
        self.__chunk_size = multiple

    def set_verbose_mode(self, verbose):
        """
        output merging information

        :param verbose: boolean
        :return: None
        """
        self.__verbose = verbose

    def run(self):
        self.__empty_output_file()
        for chunk in self.__filters():
            if (self.__anon_level > 1) and (len(chunk) >= self.__anon_level):
                chunk = self.__merge_filters(chunk)

            if self.__noise_level > 0:
                chunk = self.__noise_filters(chunk)

            self.__save_chunk(chunk)

    def __merge_filters(self, bflist):
        """
        pick groups of k filters and merge them.
        """
        split_idx = len(bflist)/self.__anon_level
        bf_idcs = range(split_idx, len(bflist))
        np.random.shuffle(bf_idcs)

        k = self.__anon_level-1
        anon_bfs = list()
        for i in range(split_idx):
            b = bflist[i]
            
            filters = list()
            for j in range(k):
                filters.append(bf_idcs.pop())
                b.merge(bflist[filters[j]])
            if self.__verbose:
                msg = "Merge Filters: {}".format(filters)
                print(msg)
            
            anon_bfs.append(b)
        
        return anon_bfs

    def __noise_filters(self, bflist):
        noise_blooms = list()
        for b in bflist:
            b.fill_with_noise(self.__noise_level)
            noise_blooms.append(b)
        return noise_blooms

    def __save_chunk(self, bflist):
        with open(self.__output, 'a') as f:
            for b in bflist:
                b.add_to_file(f)

    def __filters(self):
        with open(self.__input, 'r') as f:
            chunk_list = list()
            chunk_positive = list()
            chunk_negative = list()
            i = 0
            for line in f:
                i += 1
                b = BloomFilter.factory(self.__type, 0)
                try:
                    b.read_from_line(line)
                except ValueError:
                    print('Could not parse Bloom filter in line {} in file {}. Skipping.'.format(i, self.__input), file=sys.stderr)
                    continue

                if self.__merge_mode == 'train':
                    # divide filters into chunks according to labels
                    if b.get_label() == 1:
                        chunk_positive.append(b)
                    elif b.get_label() == -1:
                        chunk_negative.append(b)

                    if (len(chunk_positive) > 0) and ((len(chunk_positive) % self.__anon_level) == 0):
                        yield chunk_positive
                        chunk_positive = list()
                    elif (len(chunk_negative) > 0) and ((len(chunk_negative) % self.__anon_level) == 0):
                        yield chunk_negative
                        chunk_negative = list()
                else:
                    # ignore labels when anonymizing test dataset
                    if b.get_label() != 0:
                        chunk_list.append(b)
                    if (len(chunk_list) > 0) and ((len(chunk_list) % self.__anon_level) == 0):
                        yield chunk_list
                        chunk_list = list()

    def __empty_output_file(self):
        with open(self.__output, 'w'):
            pass

