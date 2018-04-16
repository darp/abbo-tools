import mmh3
import json

from abstract_double_hash_bloom import AbstractDoubleHashBloomFilter


class MurmurBloomFilter(AbstractDoubleHashBloomFilter):

    def __init__(self, num_bits):
        super(MurmurBloomFilter, self).__init__(num_bits)

    def _hash_func1(self, elem):
        return mmh3.hash(json.dumps(elem, ensure_ascii=True), 0)

    def _hash_func2(self, elem):
        hash1 = self._hash_func1(elem)
        return mmh3.hash(json.dumps(elem, ensure_ascii=True), hash1)
