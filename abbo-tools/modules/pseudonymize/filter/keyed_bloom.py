import hmac
import hashlib
import json

from abstract_double_hash_bloom import AbstractDoubleHashBloomFilter


class KeyedBloomFilter(AbstractDoubleHashBloomFilter):

    def __init__(self, num_bits, encryption_key):
        super(KeyedBloomFilter, self).__init__(num_bits)
        self.__encryption_key = encryption_key

    def _hash_func1(self, elem):
        return int(hmac.new(self.__encryption_key, json.dumps(elem, ensure_ascii=True), hashlib.md5).hexdigest(), 16)

    def _hash_func2(self, elem):
        return int(hmac.new(self.__encryption_key, json.dumps(elem, ensure_ascii=True), hashlib.sha1).hexdigest(), 16)
