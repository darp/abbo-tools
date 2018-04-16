def calc_double_hash(unsigned long long hash1, unsigned long long hash2, int num_bits, int num_hashes):
    hash_list = [abs((hash1 + i*hash2) % num_bits) for i in range(num_hashes)]
    return hash_list