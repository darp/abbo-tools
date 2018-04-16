from modules.pseudonymize.filter.bloom_factory import BloomFilter


class LIBSVMConverter(object):

    def __init__(self):
        self.__label = None
        self.__input = None
        self.__output = None

    def set_input_file(self, input_file):
        self.__input = input_file

    def set_output_file(self, output_file):
        self.__output = output_file

    def run(self):
        with open(self.__output, 'w') as outfile:
            with open(self.__input, 'r') as infile:
                for line in infile:
                    b = BloomFilter.factory("", 16)
                    b.read_from_line(line)
                    outfile.write('{}\n'.format(b.get_libsvm_str()))
