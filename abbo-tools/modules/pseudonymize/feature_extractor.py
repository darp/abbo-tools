from __future__ import print_function
import os
import re
import simplejson
import itertools
import urllib2
from filter.bloom_factory import BloomFilter
import sys
import logging

"""
read relevant features from given orders in JSON format
and store them in bloom filters
"""


class FeatureExtractor(object):

    def __init__(self):
        self.__input = None
        self.__output = None
        self.__order_fields = ['billingAddress',
                               'cartItems',
                               'couponCode',
                               'customer',
                               'grandTotal',
                               'iteration',
                               'openAmount',
                               'shippingAddress',
                               'solvencyScore']
        self.__bloom_filter_size = 1024  # number of bits in Bloom filter
        self.__bloom_filter_type = 'murmur'
        self.__encryption_key = ""
        self.__bin_sizes = {'price': 5,
                            'solvencyScore': 1,
                            'iteration': 1,
                            'openAmount': 50,
                            'grandTotal': 50}

        self.__decomposition_type = 'words'
        self.__ngram_len = 3
        self.__hash_num = 3
        self.__mapping_file = None
        self.__logger = None

    def set_input(self, input):
        """
        input file containing orders in JSON format separated by newline characters

        :param input: name file
        :return: None
        """
        self.__input = input

    def set_output(self, output):
        """
        output file where bloom filters and corresponding labels are stored separated by newlines

        :param output: name of file
        :return: None
        """
        self.__output = output

    def set_bloomfilter_size(self, size):
        """
        set capacity of bloom filters

        :param size: int
        :return: None
        """
        self.__bloom_filter_size = size

    def set_bloomfilter_type(self, bloom_filter_type):
        """
        set type of Bloom filters

        :param bloom_filter_type: str ('murmur', 'keyed')
        :return: None
        """
        self.__bloom_filter_type = bloom_filter_type

    def set_encryption_key(self, encryption_key):
        """
        set encryption key for Bloom filters with keyed hash functions

        :param encryption_key: str
        :return: None
        """
        self.__encryption_key = encryption_key

    def set_decomposition_type(self, decomposition_type):
        """
        set type of decomposition (ngrams, words, entities)

        :param decomposition_type: str
        :return: None
        """
        self.__decomposition_type = decomposition_type

    def set_ngram_length(self, ngram_len):
        """
        set length of ngrams

        :param ngram_len: int
        :return: None
        """
        self.__ngram_len = ngram_len

    def set_num_of_hash_funcs(self, hash_num):
        """
        set number of hash functions for bloom filter

        :param hash_num: int
        :return: None
        """
        self.__hash_num = hash_num

    def set_bin_sizes(self, bin_sizes):
        """
        set bin sizes for feature discretization

        :param bin_sizes: dict with bin_sizes
        :return: None
        """
        self.__bin_sizes.update(bin_sizes)

    def set_mapping_file(self, mapping_file):
        """
        set mapping file to store mapping between elements and
        bits set in Bloom filters

        :param mapping_file: str
            path to mapping file
        :return: None
        """
        if mapping_file is not None:
            self.__mapping_file = os.path.abspath(mapping_file)

    def run(self):
        """
        read orders stored in JSON format and create bloom filters.
        bloom filters are stored Base64 encoded in a single file.
        """
        self._pseudonymize()

    def _pseudonymize(self):
        outfile = open(self.__output, 'w')
        with open(self.__input, 'r') as in_file:
            mapping = dict()
            i, num_lines = 1, sum(1 for line in open(self.__input, 'r'))
            for line in in_file:
                try:
                    order = simplejson.loads(line, encoding='utf-8')
                    feat_str = self._json_to_str(order).strip()

                    if self.__logger is not None:
                        self.__logger.debug(feat_str)

                    # create bloom filter
                    b = BloomFilter.factory(self.__bloom_filter_type,
                                            self.__bloom_filter_size,
                                            self.__encryption_key)
                    b.set_num_hash_functions(self.__hash_num)
                    for word in re.split(" ", feat_str):
                        hashes = b.add(word)

                        if self.__mapping_file:
                            if word not in mapping:
                                mapping[word] = hashes

                    b.set_label(order.get('invoiceFraudLabel'))
                    b.add_to_file(outfile)
                except Exception as e:
                    outfile.write("NOT AVAILABLE\n")
                    print("An error occured while pseudonymizing order in line {}: {}".format(i, e), file=sys.stderr)
                i += 1
        outfile.close()

        if self.__mapping_file:
            self.__save_mapping(mapping)

    def __save_mapping(self, mapping):
        with open(self.__mapping_file, 'w') as fout:
            fout.write('decomposition_type:{}\n'.format(self.__decomposition_type))
            fout.write('ngram_len:{}\n'.format(self.__ngram_len))
            fout.write('bin_sizes:{}\n'.format(self.__bin_sizes))
            for k, v in mapping.items():
                s = u'{}:{}\n'.format(k, v)
                fout.write(s.encode('utf-8'))

    def _json_to_str(self, json_dict):
        if self.__decomposition_type == 'ngrams':
            return self._get_ngram_string(json_dict, prefix=False)
        elif self.__decomposition_type == 'colored':
            return self._get_ngram_string(json_dict, prefix=True)
        elif self.__decomposition_type == 'entities':
            return self._get_words_string(json_dict, delim='_', prefix=True)
        else:
            return self._get_words_string(json_dict, delim=' ', prefix=False)

    @staticmethod
    def _add_prefix(prefix, string):
        return u'{}{}'.format(prefix, string)

    def _get_ngram_string(self, json_dict, prefix):
        if prefix:
            ngrams = list()
            feat_str = self._get_words_string(json_dict, delim='_', prefix=True)
            for entity in feat_str.split(' '):
                pref, feat = entity.split('->')
                feat = feat.replace(' ', '_')
                if pref.find('customer') >= 0 or pref.find('Address') >= 0:
                    entity_ngrams = [''.join(e) for e in zip(*[feat[i:] for i in range(self.__ngram_len)])]
                    ngrams += map('->'.join, itertools.chain(itertools.product([pref], entity_ngrams)))
                elif pref.find('cartItem') >= 0:
                    item, price = feat.split('_')
                    item_ngrams = [''.join(e) for e in zip(*[item[i:] for i in range(self.__ngram_len)])]
                    ngrams += map('->'.join, itertools.chain(itertools.product([pref], item_ngrams)))
                    ngrams += [u'cartItem->{}'.format(price)]
                else:
                    ngrams += [u'{}->{}'.format(pref, feat)]
        else:
            feat_str = self._get_words_string(json_dict, delim='_', prefix=False).replace(' ', '_')
            ngrams = [''.join(e) for e in zip(*[feat_str[i:] for i in range(self.__ngram_len)])]
        return ' '.join(ngrams)

    def _get_words_string(self, json_dict, delim, prefix=False):
        str_list = list()
        for field in sorted(self.__order_fields):

            if field not in json_dict:
                continue

            if field.find('customer') >= 0:
                prefix_str = 'customer->' if prefix else ''
                str_list.append(self.__get_customer_string(json_dict['customer'], delim, prefix_str))
            elif field.find('Address') >= 0:
                prefix_str = '{}->'.format(field) if prefix else ''
                str_list.append(self.__get_address_string(json_dict[field], delim, prefix_str))
            elif field == 'cartItems':
                str_list.append(self.__get_cart_items_string(json_dict['cartItems'], delim, prefix))
            elif field == 'couponCode':
                prefix_str = 'couponCode->' if prefix else ''
                feat_str = u'{}{}'.format(prefix_str, self.__get_coupon_code_string(json_dict['couponCode']))
                str_list.append(feat_str)
            elif field == 'solvencyScore':
                prefix_str = 'solvencyScore->' if prefix else ''
                feat_str = u'{}{}'.format(prefix_str, self.__get_solvency_score_string(json_dict['solvencyScore']))
                str_list.append(feat_str)
            elif field == 'grandTotal':
                prefix_str = 'grandTotal->' if prefix else ''
                feat_str = u'{}{}'.format(prefix_str, FeatureExtractor.__discretize(float(json_dict['grandTotal']),
                                                                                    float(self.__bin_sizes['grandTotal'])))
                str_list.append(feat_str)
            elif field == 'openAmount':
                prefix_str = 'openAmount->' if prefix else ''
                feat_str = u'{}{}'.format(prefix_str, FeatureExtractor.__discretize(float(json_dict['openAmount']),
                                                                                    float(self.__bin_sizes['openAmount'])))
                str_list.append(feat_str)
            elif field == 'iteration':
                prefix_str = 'iteration->' if prefix else ''
                feat_str = u'{}{}'.format(prefix_str, u'{}'.format(json_dict[field]))
                str_list.append(feat_str)
        return ' '.join(str_list)

    @staticmethod
    def __get_customer_string(customer_dict, delim, prefix=''):
        valid_keys = {'email', 'gender', 'firstName', 'lastName'}
        cstr_list = list()
        for key, value in sorted(customer_dict.items()):
            if key in valid_keys:
                cstr_list.append(u'{}{}'.format(prefix, value).replace(' ', delim))
        return ' '.join(cstr_list)

    @staticmethod
    def __get_address_string(address_dict, delim, prefix=''):
        valid_keys = {'firstName', 'lastName', 'street', 'zip'}
        astr_list = list()
        for key, value in sorted(address_dict.items()):
            if key in valid_keys:
                astr_list.append(u'{}{}'.format(prefix, value).replace(' ', delim))
        return ' '.join(astr_list)

    def __get_cart_items_string(self, cart_items, delim, prefix=False):
        """
        sorts cart items in ascending order using their price
        """
        cstr_list = list()
        for item in sorted(cart_items, key=lambda x: x['price']):
            price = FeatureExtractor.__discretize(float(item['price']), float(self.__bin_sizes['price']))
            prefix_str = 'cartItem->' if prefix else ''
            item_str = urllib2.quote(item['articleSimpleSKU'].replace('_', ' '))
            cstr_list.append(u'{}{}{}{}'.format(prefix_str, item_str, delim, price))
        return ' '.join(cstr_list)

    @staticmethod
    def __get_coupon_code_string(coupon_code):
        return u'{}'.format(str(coupon_code != ""))

    def __get_solvency_score_string(self, solvency_score):
        return u'{}'.format(FeatureExtractor.__discretize(solvency_score['score'], float(self.__bin_sizes['solvencyScore'])))

    @staticmethod
    def __discretize(value, bin_size):
        """
        use discrete values e.g. for prices, scores where the
        discretization granularity is given by the bin size
        """
        return_val = 'null'
        if value is not None:
            return_val = str(round(value/float(bin_size)) * bin_size)
        return return_val

    def set_log_file(self, logfile):
        """
        init logfile for feature extraction class

        :param logfile: string
        :return: None
        """
        if logfile is not None:
            logging.basicConfig(filename=logfile, filemode='w', level=logging.DEBUG)
            self.__logger = logging.getLogger('feature_extractor')
