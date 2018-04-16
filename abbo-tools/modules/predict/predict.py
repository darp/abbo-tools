import os
import string
import scipy.sparse as sp
import numpy as np
from sklearn.datasets import load_svmlight_file


class PredictionModule(object):

    def __init__(self):
        self.__model_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/toy.model')
        self.__input_file = None
        self.__output_file = None
        self.__mapping_file = None
        self.__explaination_file = None

    def run(self):
        """
        output prediction scores for pseudonymized orders
        in a given file. File has to be in LIBSVM format
        (one order per line).

        :param input_file: file in LIBSVM format
        :return: None
        """
        w = self.__load_liblinear_model()
        X, y = self.__load_data()
        pred_scores, pred_labels, results = self.__predict_fraud(w, X, y)
        self.__output_results(pred_scores, pred_labels, results)
        if self.__explaination_file:
            self.__get_explainations(w)

    def set_input(self, input_file):
        """
        Set file containing data set in LIBSVM format

        :param input_file: str
        :return: None
        """
        self.__input_file = os.path.abspath(input_file)

    def set_output(self, output_file):
        """
        Set output file to store detailed prediction results

        :param output_file: str
        :return: None
        """
        if output_file is not None:
            self.__output_file = os.path.abspath(output_file)

    def set_model(self, model_file):
        """
        Set custom LIBLINEAR model

        :param model_file: str
        :return: None
        """
        if model_file is not None:
            self.__model_file = os.path.abspath(model_file)

    def set_explaination_files(self, mapping_file, explaination_file):
        """
        Set files for deriving explainations for the decisions
        of the classifier
        :param mapping_file: str
            File containing mapping between elements to positions in Bloom filter
        :param explaination_file:
            File to store most relevant elements for
        :return:
        """
        self.__mapping_file = os.path.abspath(mapping_file)
        self.__explaination_file = os.path.abspath(explaination_file)

    def __load_liblinear_model(self):
        """
        load liblinear model and store it
        in Scipy sparse matrix

        :return: scipy.sparse.csr_matrix
        """
        with open(self.__model_file, 'rb') as model:
            w = map(float, map(string.strip, model.readlines()[6:]))
        return sp.csr_matrix(w)

    def __load_data(self):
        data = load_svmlight_file(self.__input_file)
        return data[0], data[1]

    def __predict_fraud(self, w, X, y):
        """
        Predict scores and labels for a given data
        X using a classification model w. Comparison
        with ground truth labels y.

        :param w: scipy.sparse.csr.csr_matrix
            The linear SVM model
        :param X: scipy.sparse.csr.csr_matrix
            The dataset vectors
        :param y: numpy.ndarray
            The dataset labels
        :return: scores (scipy sparse matrix),
                 predicted labels (np.ndarray),
                 detection results (np.ndarray)

        """
        scores = w * X.T

        # calc labels
        pred_y = -1.0 * np.ones(y.shape)
        idcs = sp.find(scores > 0)[1]
        pred_y[idcs] = 1.0

        results = (pred_y == y)

        return scores, pred_y, results

    def __output_results(self, pred_scores, pred_labels, results):
        """
        Output prediction results

        :param pred_scores:
        :param pred_labels:
        :param results: np.ndarray
        :return: None
        """
        accuracy = len(np.where(results == True)[0]) * 100.0 / len(results)
        print("Accuracy = {}%".format(accuracy))

        # write detailed results into output file if provided
        if self.__output_file is not None:
            with open(self.__output_file, 'w') as f:
                f.write('label,score\n')
                for i in range(len(pred_labels)):
                    f.write('{},{}\n'.format(pred_labels[i], pred_scores[0, i]))

    def __get_explainations(self, w):
        """
        Extract patterns mostly indicative for fraud

        :param w: scipy.sparse.csr.csr_matrix
            The linear SVM model
        :return: None
            Results are written to explainability files
        """
        item2score = dict()
        with open(self.__mapping_file, 'r') as fin:
            for line in fin.readlines()[3:]:
                item, hashes = line.strip().split(':')
                score = 0.0
                for hash in map(int, map(long, hashes[1:-1].split(','))):
                    score += w[0, hash]
                item2score[item] = score

        with open(self.__explaination_file, 'w') as fout:
            fout.write('item,score\n')
            for k, v in sorted(item2score.items(), key=lambda x: x[1], reverse=True):
                fout.write('{},{}\n'.format(k, v))


