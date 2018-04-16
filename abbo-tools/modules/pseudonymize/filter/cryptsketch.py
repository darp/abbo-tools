import hmac
import hashlib
import json

from keyed_cmsketch import CountMinSketchFilter


class KeyedCountMin(CountMinSketchFilter):

    def __init__(self, num_bits, encryption_key):
        super(KeyedCountMin, self).__init__(num_bits)
        self.__encryption_key = encryption_key

    def _hash_func1(self, elem):
        return int(hmac.new(self.__encryption_key, json.dumps(elem, ensure_ascii=True), hashlib.md5).hexdigest(), 16)

    def _hash_func2(self, elem):
        return int(hmac.new(self.__encryption_key, json.dumps(elem, ensure_ascii=True), hashlib.sha1).hexdigest(), 16)
