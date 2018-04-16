import abc


class AbstractFilter(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractmethod
    def set_label(self, label):
        """
        set label of the filter

        :param label: int
        :return: None
        """
        pass

    @abc.abstractmethod
    def get_label(self):
        """
        get the label of the filter
        :return: int
        """
        pass

    @abc.abstractproperty
    def size(self):
        """
        returns the size of the filter

        :return: int
        """
        pass

    @abc.abstractproperty
    def fill_level(self):
        """
        returns fill level of the filter

        :return: int
        """
        pass

    @abc.abstractmethod
    def add(self, elem):
        """
        add string element to the filter

        :param elem: str
        :return: None
        """
        pass

    @abc.abstractmethod
    def add_to_file(self, f):
        """
        append Base64 encoded representation of filter to file

        :param f: file object
        :return: None
        """
        pass

    def read_from_line(self, line):
        """
        converts Base64 encoded representation of filter
        to interal representation (e.g. numpy array or bitarray)

        :param line: label<TAB>base64encoded_filter
        :return: None
        """
        pass

    @abc.abstractmethod
    def fill_with_noise(self, noise_level):
        """
        fill filter with random noise in order to
        impede a depseudonymization attack.

        :param noise_level: noise level in percent (float)
        :return: None
        """
        pass

    @abc.abstractmethod
    def to_numpy_array(self):
        """
        converts filter to numpy row vector

        :return: numpy.ndarray
        """
        pass

    @abc.abstractmethod
    def get_libsvm_str(self):
        """
        output filter filter in LIBSVM format

        :return: str
        """
        pass

    @abc.abstractmethod
    def calc_similarity(self, other):
        """
        output similarity to other filter

        :param other: object of type AbstractFilter
        :return: double
        """
        pass

    @abc.abstractmethod
    def merge(self, other):
        """
        merge with another filter

        :param other: object of type AbstractFilter
        :return: None
        """
        pass
