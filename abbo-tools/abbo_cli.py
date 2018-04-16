#!/usr/bin/env python
"""
Command line interface for the ABBO analysis toolbox
"""
import sys
import argparse
import simplejson as json

from modules.convert.converter import LIBSVMConverter
from modules.generate.data_generator import SampleDataGenerator
from modules.pseudonymize.feature_extractor import FeatureExtractor
from modules.hardening.hardening import HardeningModule
from modules.predict.predict import PredictionModule


DESCRIPTION = """
***********************************************
   _   ___ ___  ___     ___ _    ___
  /_\ | _ ) _ )/ _ \   / __| |  |_ _|
 / _ \| _ \ _ \ (_) | | (__| |__ | |
/_/ \_\___/___/\___/   \___|____|___| (v0.3.3)

***********************************************
"""


class ABBOCommandLineInterface(object):

    def __init__(self):
        self.command = None

    def run(self):
        self._parse()
        self._run()

    def _parse(self):
        # sub command functions
        def _convert(args):
            self.command = 'convert'

        def _generate(args):
            self.command = 'generate'

        def _hardening(args):
            self.command = 'hardening'

        def _pseudonymize(args):
            self.command = 'pseudonymize'

        def _predict(args):
            self.command = 'predict'

        # create top level parser
        parser = argparse.ArgumentParser(description=DESCRIPTION,
                                         formatter_class=argparse.RawTextHelpFormatter)
        subparsers = parser.add_subparsers(help="Available commands")
        subparsers.required = True

        # convert into compatible file format
        convert = subparsers.add_parser('convert', help="convert input file to LIBSVM format")
        convert.set_defaults(func=_convert)
        convert.add_argument('input_file', type=str,
                             help="file containing orders in JSON format")
        convert.add_argument('output_file', type=str,
                             help="File with orders in LIBSVM format")

        # generate sample data
        generate = subparsers.add_parser('generate', help="Generate artificial data")
        generate.set_defaults(func=_generate)
        generate.add_argument('output_file', type=str,
                              help="File to store generated orders in JSON format")
        generate.add_argument('-c', '--num_customers', type=int, default=100,
                              help="Size of customer pool")
        generate.add_argument('-n', '--num_orders', type=int, default=100,
                              help="Number of orders in each dataset")
        generate.add_argument('-s', '--seed', type=int, default=None,
                              help="Set seed")
        generate.add_argument('-u', '--upper', action='store_true', default=None,
                              help="Only use upper case letters.")
        generate.add_argument('-p', '--fraud_probability', type=float, default=0.5,
                              help="Set fraud probability.")
        generate.add_argument('--simple', action='store_true', default=None,
                              help="Generate orders only containing billing address information.")
        generate.add_argument('--unique_customers', action='store_true', default=None,
                              help="Customers are sampled without replacement.")

        # pseudonymize input data
        pseudonymize = subparsers.add_parser('pseudonymize', help="Pseudonymize orders")
        pseudonymize.set_defaults(func=_pseudonymize)
        pseudonymize.add_argument('input_file', type=str,
                                  help="File containing orders in JSON format")
        pseudonymize.add_argument('output_file', type=str,
                                  help="Output file to store pseudonymized orders")
        pseudonymize.add_argument('-m', '--bloom_filter_size', type=int, default=1024,
                                  help="Number of bits in Bloom Filter")
        pseudonymize.add_argument('-d', '--decomposition', type=str,
                                  choices=['entities', 'colored', 'ngrams', 'words'],
                                  default='words', help="Type of decomposition")
        pseudonymize.add_argument('-n', '--ngram_len', type=int, default=2,
                                  help="Length of ngrams")
        pseudonymize.add_argument('-k', '--hash_num', type=int, default=3,
                                  help="Number of hash functions used in Bloom Filter")
        pseudonymize.add_argument('-t', '--bloom_filter_type', type=str,
                                  choices=['murmur', 'keyed', 'count', 'keyedcount'], default='murmur',
                                  help="Use Bloomfilters or Count-Min-Sketches")
        pseudonymize.add_argument('-e', '--encryption_key', type=str, default='',
                                  help="Set encryption key for keyed hash functions")
        pseudonymize.add_argument('-b', '--bin_sizes', type=json.loads, default=dict(),
                                  help="Set bin sizes for feature discretization.")
        pseudonymize.add_argument('--logging', type=str, default=None,
                                  help="Set file to log debug messages.")
        pseudonymize.add_argument('--mapping_file', type=str, default=None,
                                  help="Write mappping to file.")

        # hardening
        hardening = subparsers.add_parser('hardening', help="Apply hardening mechanisms to given bloom filters")
        hardening.set_defaults(func=_hardening)
        hardening.add_argument('input_file', type=str,
                               help="File containing bloom filters in CSV format")
        hardening.add_argument('output_file', type=str,
                               help="File in which to store modified filters")
        hardening.add_argument('-n', '--noise_level', type=float, default=0.0,
                               help="Add random noise (0 <= noise <= 100). ")
        hardening.add_argument('-m', '--merging_mode', type=str,
                               choices=['train', 'test'], default='test',
                               help="Merge in \'train\' mode only entries with the same label. \
                                    Ignore labels in \'test\' mode.")
        hardening.add_argument('-t', '--filter_type', type=str,
                               choices=['murmur', 'keyed', 'count', 'keyedcount'], default='murmur',
                               help="Set filter type (bloom filter or count-min sketch)")
        hardening.add_argument('-l', '--merging_level', type=int, default=1,
                               help="Set merge level (default k=1, i.e. no merging)")
        hardening.add_argument('-v', '--verbose_mode', action='store_true', default=False,
                               help="Output list of merged filters")
        hardening.add_argument('-s', '--chunk_size', type=int, default=100,
                               help="Set size of chunks in which data are processed")

        # prediction
        predict = subparsers.add_parser('predict', help="Predict class labels for unknown orders")
        predict.set_defaults(func=_predict)
        predict.add_argument('input_file', type=str, help="File containing data in LIBSVM format.")
        predict.add_argument('-m', '--model_file', type=str, default=None,
                             help="Set custom LIBLINEAR model.")
        predict.add_argument('-o', '--output_file', type=str, default=None,
                             help="Store detailed results in output file.")
        predict.add_argument('--mapping_and_patterns_file', type=str, nargs=2, default=None,
                             help="Provide files for retrieving explaination of classifier decisions.")

        self.args = parser.parse_args()
        self.args.func(self.args)

    def _run(self):
        getattr(self, '_cmd_{}'.format(self.command))()

    def _cmd_convert(self):
        converter = LIBSVMConverter()
        converter.set_input_file(self.args.input_file)
        converter.set_output_file(self.args.output_file)
        converter.run()

    def _cmd_generate(self):
        s = SampleDataGenerator(self.args.output_file, self.args.seed)
        s.set_num_of_orders(self.args.num_orders)
        s.set_num_of_customers(self.args.num_customers)
        s.use_upper_case(self.args.upper)
        s.set_simple_mode(self.args.simple)
        s.set_fraud_probability(self.args.fraud_probability)
        s.set_unique_customers(self.args.unique_customers)
        s.run()

    def _cmd_pseudonymize(self):
        feat_extr = FeatureExtractor()
        feat_extr.set_input(self.args.input_file)
        feat_extr.set_output(self.args.output_file)
        feat_extr.set_bloomfilter_type(self.args.bloom_filter_type)
        feat_extr.set_encryption_key(self.args.encryption_key)
        feat_extr.set_decomposition_type(self.args.decomposition)
        feat_extr.set_bloomfilter_size(self.args.bloom_filter_size)
        feat_extr.set_ngram_length(self.args.ngram_len)
        feat_extr.set_num_of_hash_funcs(self.args.hash_num)
        feat_extr.set_bin_sizes(self.args.bin_sizes)
        feat_extr.set_log_file(self.args.logging)
        feat_extr.set_mapping_file(self.args.mapping_file)
        feat_extr.run()

    def _cmd_hardening(self):
        hardening = HardeningModule()
        hardening.set_input(self.args.input_file)
        hardening.set_output(self.args.output_file)
        hardening.set_filter_type(self.args.filter_type)
        hardening.set_merging_level(self.args.merging_level)
        hardening.set_noise_level(self.args.noise_level)
        hardening.set_chunk_size(self.args.chunk_size)
        hardening.set_merging_mode(self.args.merging_mode)
        hardening.run()

    def _cmd_predict(self):
        prediction_module = PredictionModule()
        prediction_module.set_input(self.args.input_file)
        prediction_module.set_output(self.args.output_file)
        prediction_module.set_model(self.args.model_file)
        if self.args.mapping_and_patterns_file:
            prediction_module.set_explaination_files(self.args.mapping_and_patterns_file[0],
                                                     self.args.mapping_and_patterns_file[1])
        prediction_module.run()


def main_func():
    sys.exit(ABBOCommandLineInterface().run())


if __name__ == '__main__':
    main_func()

