import unittest
import os
import numpy as np

from modules.pseudonymize.filter.bloom_factory import BloomFilter


class MurmurBloomTestClass(unittest.TestCase):

    bloom_type = "murmur"
    key = "default"

    def setUp(self):
        self._bf0 = BloomFilter.factory(self.bloom_type, 20, self.key)
        self._bf1 = BloomFilter.factory(self.bloom_type, 44, self.key)

    def test_init_size(self):
        bfa = self._bf0.to_numpy_array()
        self.assertEqual(bfa.shape[0], 24)

    def test_init_zero(self):
        bfa = self._bf0.to_numpy_array()
        self.assertEqual(np.sum(bfa), 0)

    def test_num_hash_functions(self):
        self._bf0.set_num_hash_functions(4)
        self._bf0.add('test')
        bfa = self._bf0.to_numpy_array()
        self.assertEqual(np.sum(bfa), 4)

    def test_add_element(self):
        self._bf0.add('test')
        self.assertTrue(self._bf0.contains('test'))
        self.assertFalse(self._bf0.contains('mimimi'))

    def test_add_to_file(self):
        # fill bloom filters
        self._bf0.add('test')
        self._bf0.add('dings')
        self._bf1.add('test2')
        self._bf1.add('dings2')

        with open('test.txt', 'w') as f:
            self._bf0.add_to_file(f)
            self._bf1.add_to_file(f)

        bf_list = list()
        with open('test.txt', 'r') as f:
            for line in f:
                bf = BloomFilter.factory(self.bloom_type, 8, self.key)
                bf.read_from_line(line)
                bf_list.append(bf)
        os.remove('test.txt')

        for i in range(2):
            bf0 = getattr(self, '_bf{}'.format(i))
            bf1 = bf_list[i]

            # convert to numpy arrays
            bfa0 = bf0.to_numpy_array()
            bfa1 = bf1.to_numpy_array()

            self.assertEqual(bfa0.shape[0], bfa1.shape[0])
            self.assertTrue((bfa0 == bfa1).all())


    def test_similarity_measure(self):
        self._bf0 = BloomFilter.factory(self.bloom_type, 100, self.key)
        self._bf1 = BloomFilter.factory(self.bloom_type, 100, self.key)
        self._bf2 = BloomFilter.factory(self.bloom_type, 100, self.key)

        self._bf0.add('test')
        self._bf0.add('test')
        self._bf0.add('test2')

        self._bf1.add('test')
        self._bf1.add('test')
        self._bf1.add('test2')

        self._bf2.add('test1')
        self._bf2.add('test1')
        self._bf2.add('test1')

        self.assertEqual(self._bf0.calc_similarity(self._bf1), 0.0)
        self.assertEqual(self._bf0.calc_similarity(self._bf2), 1.0)

        self.assertTrue(self._bf0.calc_similarity(self._bf1, 'simple') == 0.0)
        self.assertTrue(self._bf0.calc_similarity(self._bf2, 'simple') > 0.0)


class CryptoBloomTestClass(MurmurBloomTestClass):

    bloom_type = "keyed"
    key = "crypt_key"


class CountMinSketchTestClass(unittest.TestCase):

    bloom_type = "count"
    key = "default"

    def setUp(self):
        self._cm0 = BloomFilter.factory(self.bloom_type, 30, self.key)

    def test_init_size(self):
        cma = self._cm0.to_numpy_array()
        self.assertEqual(len(cma), 30)

    def test_init_zero(self):
        cma = self._cm0.to_numpy_array()
        self.assertEqual(np.sum(cma), 0)

    def test_num_hash_functions(self):
        self._cm0.set_num_hash_functions(3)
        self._cm0.add('test')
        cma = self._cm0.to_numpy_array()
        self.assertEqual(np.sum(cma), 3)

    def test_add_multiple_elements(self):
        self._cm0.add('test')
        self._cm0.add('test')
        self._cm0.add('test')
        self._cm0.add('test2')
        self.assertEqual(self._cm0.get_num_of_inserts('test'), 3)
        self.assertEqual(self._cm0.get_num_of_inserts('test2'), 1)
        self.assertEqual(self._cm0.get_num_of_inserts('mimimi'), 0)

    def test_add_to_file(self):
        # fill bloom filters
        self._cm0.add('test')
        self._cm0.add('test')
        self._cm0.add('dings')

        with open('test.txt', 'w') as f:
            self._cm0.add_to_file(f)

        bf_list = list()
        with open('test.txt', 'r') as f:
            for line in f:
                cm = BloomFilter.factory(self.bloom_type, 8, self.key)
                cm.read_from_line(line)
                bf_list.append(cm)
        os.remove('test.txt')

        cm0 = self._cm0
        cm1 = bf_list[0]

        # get numpy arrays
        cma0 = cm0.to_numpy_array()
        cma1 = cm1.to_numpy_array()

        self.assertEqual(cma0.shape[0], cma1.shape[0])
        self.assertTrue((cma0 == cma1).all())

    def test_similarity_measure(self):
        self._cm0.add('test')
        self._cm0.add('test')
        self._cm0.add('test2')

        self._cm1 = BloomFilter.factory(self.bloom_type, 30, self.key)
        self._cm2 = BloomFilter.factory(self.bloom_type, 30, self.key)

        self._cm1.add('test')
        self._cm1.add('test')
        self._cm1.add('test2')

        self._cm2.add('test1')
        self._cm2.add('test1')
        self._cm2.add('test1')

        self.assertEqual(self._cm0.calc_similarity(self._cm1), 0.0)
        self.assertEqual(self._cm0.calc_similarity(self._cm2), 1.0)

        self.assertEqual(self._cm0.calc_similarity(self._cm1, 'simple'), 0.0)
        self.assertEqual(self._cm0.calc_similarity(self._cm2, 'simple'), 1.0)


class CryptoCountMinSketchTestClass(CountMinSketchTestClass):

    bloom_type = "keyedcount"
    key = "crypt_key"


if __name__ == '__main__':
    unittest.main()

