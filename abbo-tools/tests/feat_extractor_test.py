import unittest

from modules.pseudonymize.feature_extractor import FeatureExtractor


class FeatureExtractorUnitTest(FeatureExtractor):

    def get_words_string(self, json_dict):
        return self._get_words_string(json_dict, delim=' ', prefix=False)

    def get_entities_string(self, json_dict):
        return self._get_words_string(json_dict, delim='_', prefix=True)

    def get_ngram_string(self, json_dict):
        return self._get_ngram_string(json_dict, prefix=False)

    def get_colored_ngram_string(self, json_dict):
        return self._get_ngram_string(json_dict, prefix=True)


class FeatureExtractorTest(unittest.TestCase):

    def setUp(self):
        self.order = {'billingAddress': {'firstName': 'bfname',
                                         'lastName': 'blname',
                                         'street': 'bstreet name',
                                         'zip': 'bzip'},
                      'cartItems': [{'price': 1977.0,
                                     'articleSimpleSKU': 'GstQ'},
                                    {'price': 1986.0,
                                     'articleSimpleSKU': 'MoP'}],
                      'couponCode': 'ccode',
                      'customer': {'firstName': 'cfname',
                                   'lastName': 'clname',
                                   'email': 'dings@dangs.com',
                                   'gender': 'f'},
                      'grandTotal': 1978.0,
                      'iteration': 1,
                      'openAmount': 2.0,
                      'shippingAddress': {'firstName': 'sfname',
                                          'lastName': 'slname',
                                          'street': 'sstreet',
                                          'zip': 'szip'},
                      'solvencyScore': {'score': 3.0}}

    def test_word_decomposition(self):
        fe = FeatureExtractorUnitTest()
        fe.set_bin_sizes({'price': 10,
                          'solvencyScore': 5,
                          'iteration': 5,
                          'openAmount': 10,
                          'grandTotal': 10})
        exp_str = "bfname blname bstreet name bzip " \
                  "GstQ 1980.0 MoP 1990.0 " \
                  "True " \
                  "dings@dangs.com cfname f clname " \
                  "1980.0 " \
                  "1 " \
                  "0.0 " \
                  "sfname slname sstreet szip " \
                  "5.0"
        words_str = fe.get_words_string(self.order)
        self.assertEqual(words_str, exp_str)

    def test_entities_decomposition(self):
        fe = FeatureExtractorUnitTest()
        fe.set_bin_sizes({'price': 10,
                          'solvencyScore': 5,
                          'iteration': 5,
                          'openAmount': 10,
                          'grandTotal': 10})
        exp_str = "billingAddress->bfname billingAddress->blname billingAddress->bstreet_name " \
                  "billingAddress->bzip " \
                  "cartItem->GstQ_1980.0 cartItem->MoP_1990.0 " \
                  "couponCode->True " \
                  "customer->dings@dangs.com " \
                  "customer->cfname " \
                  "customer->f " \
                  "customer->clname " \
                  "grandTotal->1980.0 " \
                  "iteration->1 " \
                  "openAmount->0.0 " \
                  "shippingAddress->sfname " \
                  "shippingAddress->slname " \
                  "shippingAddress->sstreet " \
                  "shippingAddress->szip " \
                  "solvencyScore->5.0"
        ent_str = fe.get_entities_string(self.order)
        self.assertEqual(ent_str, exp_str)

    def test_ngram_decomposition(self):
        fe = FeatureExtractorUnitTest()
        fe.set_bin_sizes({'price': 10,
                          'solvencyScore': 5,
                          'iteration': 5,
                          'openAmount': 10,
                          'grandTotal': 10})
        fe.set_ngram_length(3)
        exp_str = "bfn fna nam ame me_ e_b _bl " \
                  "bln lna nam ame me_ e_b _bs " \
                  "bst str tre ree eet et_ t_n _na nam ame me_ e_b _bz " \
                  "bzi zip ip_ p_G _Gs " \
                  "Gst stQ tQ_ Q_1 _19 198 980 80. 0.0 .0_ 0_M _Mo " \
                  "MoP oP_ P_1 _19 199 990 90. 0.0 .0_ 0_T _Tr " \
                  "Tru rue ue_ e_d _di " \
                  "din ing ngs gs@ s@d @da dan ang ngs gs. s.c .co com om_ m_c _cf " \
                  "cfn fna nam ame me_ e_f _f_ f_c _cl " \
                  "cln lna nam ame me_ e_1 _19 " \
                  "198 980 80. 0.0 .0_ 0_1 _1_ " \
                  "1_0 _0. " \
                  "0.0 .0_ 0_s _sf " \
                  "sfn fna nam ame me_ e_s _sl " \
                  "sln lna nam ame me_ e_s _ss " \
                  "sst str tre ree eet et_ t_s _sz " \
                  "szi zip ip_ p_5 _5. " \
                  "5.0"
        ngram_str = fe.get_ngram_string(self.order)
        self.assertEqual(ngram_str, exp_str)

    def test_colored_ngram_decomposition(self):
        fe = FeatureExtractorUnitTest()
        fe.set_bin_sizes({'price': 10,
                          'solvencyScore': 5,
                          'iteration': 5,
                          'openAmount': 10,
                          'grandTotal': 10})
        fe.set_ngram_length(3)
        expr_str = "billingAddress->bfn billingAddress->fna billingAddress->nam billingAddress->ame " \
                   "billingAddress->bln billingAddress->lna billingAddress->nam billingAddress->ame " \
                   "billingAddress->bst billingAddress->str billingAddress->tre billingAddress->ree " \
                   "billingAddress->eet billingAddress->et_ billingAddress->t_n billingAddress->_na " \
                   "billingAddress->nam billingAddress->ame billingAddress->bzi billingAddress->zip " \
                   "cartItem->Gst cartItem->stQ cartItem->1980.0 cartItem->MoP cartItem->1990.0 " \
                   "couponCode->True " \
                   "customer->din customer->ing customer->ngs customer->gs@ customer->s@d " \
                   "customer->@da customer->dan customer->ang customer->ngs customer->gs. " \
                   "customer->s.c customer->.co customer->com customer->cfn customer->fna " \
                   "customer->nam customer->ame customer->cln customer->lna customer->nam " \
                   "customer->ame " \
                   "grandTotal->1980.0 " \
                   "iteration->1 " \
                   "openAmount->0.0 " \
                   "shippingAddress->sfn shippingAddress->fna shippingAddress->nam " \
                   "shippingAddress->ame shippingAddress->sln shippingAddress->lna " \
                   "shippingAddress->nam shippingAddress->ame shippingAddress->sst " \
                   "shippingAddress->str shippingAddress->tre shippingAddress->ree " \
                   "shippingAddress->eet shippingAddress->szi shippingAddress->zip " \
                   "solvencyScore->5.0"
        ngram_str = fe.get_colored_ngram_string(self.order)
        self.assertEqual(ngram_str, expr_str)


if __name__ == '__main__':
    unittest.main()