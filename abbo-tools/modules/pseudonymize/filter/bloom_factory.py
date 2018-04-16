from __future__ import generators
from murmurbloom import MurmurBloomFilter
from keyed_bloom import KeyedBloomFilter
from keyed_cmsketch import CountMinSketchFilter
from cryptsketch import KeyedCountMin


class BloomFilter(object):

    def factory(bloom_type, bloom_size, encryption_key=""):
        if bloom_type == "keyed":
            return KeyedBloomFilter(bloom_size, encryption_key)
        if bloom_type == "count":
            return CountMinSketchFilter(bloom_size)
        if bloom_type == "keyedcount":
            return KeyedCountMin(bloom_size, encryption_key)
        else:
            return MurmurBloomFilter(bloom_size)
    factory = staticmethod(factory)