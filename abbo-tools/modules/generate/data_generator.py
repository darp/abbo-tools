import os
from csv import DictReader
from collections import defaultdict
import string
import numpy as np
import simplejson as json
import config

from order import SimpleOrder, Article, Order, Customer, Address


class SampleDataGenerator(object):
    """
    class which is used to create sample orders using given marginal distributions
    """
    id = np.random.randint(10000000000000, 10100000000000)

    def __init__(self, output_file, seed=None):
        """
        sample orders using given marginal feature distributions provided
        in misc file.

        :return: instance of SampleDataGenerator
        """
        # read marginal distributions from csv file
        self._output_file = output_file
        self._distributions = self.__read_marginal_distributions(config.MISC)
        self._num_orders = 100  # number of orders to create
        self._num_customers = 100  # number of possible customers to sample from

        self._orders = list()
        self._customers = list()
        self._articles = dict()

        self._upper = False  # only use upper case letters
        self._simple_mode = False  # create orders with less information
        self._customers_unique = False  # if true, customers are sampled without replacement
        self._fraud_probability = 0.01

        # set seeds for random number generators
        np.random.seed(seed)

    def run(self):
        """
        creates two sets of orders using given marginal feature distributions
        provided in CSV format. Each order thereby consists of a customer and
        a list of articles. These are sampled from a list of possible
        customers/articles which are created in advance. Orders are written
        to file in JSON format.

        :return: None
        """
        # create set of customers
        self.__create_customers()
        self.__load_articles()

        # create orders
        outfile = os.path.join(self._output_file)
        self.__create_orders(outfile)

    def set_num_of_orders(self, num_orders):
        """
        set number of orders to create when invoking the run method

        :param num_orders: int
        :return: None
        """
        self._num_orders = num_orders

    def set_num_of_customers(self, num_customers):
        """
        set number of possible customers to sample from

        :param num_customers: number of possible customers
        :return: None
        """
        self._num_customers = num_customers

    def use_upper_case(self, upper):
        """
        use upper case letters when sampling names

        :param upper: bool
        :return: None
        """
        self._upper = upper

    def __clean_string(self, some_string):
        # repl = {228: 'ae', 223: 'ss', 246: 'oe', 252: 'ue'}
        repl = {u'ä': 'ae', u'ß': 'ss', u'ö': 'oe', u'ü': 'ue'}
        for c in repl.keys():
            some_string = some_string.replace(c, repl[c])
        return string.upper(some_string)

    def __create_customers(self):
        self.set_num_of_customers(self._num_customers)

        # determine fraction male/female customers
        num_female_customers = int(round(self._num_customers * self._distributions['customer.gender']['f']))
        num_male_customers = self._num_customers - num_female_customers

        # create female names
        female_names = self.__sample_forenames(config.FEMALE_NAMES, num_female_customers)
        male_names = self.__sample_forenames(config.MALE_NAMES, num_male_customers)
        surnames = self.__sample_surnames(config.SURNAMES)

        if self._upper:
            female_names = map(self.__clean_string, female_names)
            male_names = map(self.__clean_string, male_names)
            surnames = map(self.__clean_string, surnames)

        providers, frequencies = SampleDataGenerator.__load_name_frequencies(config.EMAIL_PROVIDERS)
        probabilities = frequencies / np.sum(frequencies)
        email_suffixes = list(np.random.choice(providers, self._num_customers, p=probabilities))

        for i in range(len(female_names)):
            forename, surname = female_names[i], surnames.pop()
            email = u'{}.{}@{}'.format(string.lower(forename), string.lower(surname), email_suffixes.pop())
            self._customers.append(Customer(lastname=surname,
                                            firstname=forename,
                                            email=email,
                                            gender='f'))

        for i in range(len(male_names)):
            forename, surname = male_names[i], surnames.pop()
            email = u'{}.{}@{}'.format(string.lower(forename), string.lower(surname), email_suffixes.pop())
            self._customers.append(Customer(lastname=surname,
                                            firstname=forename,
                                            email=email,
                                            gender='m'))
        self.__set_addresses()

    def __set_addresses(self):
        streets = self.__sample_street_names(config.STREET_NAMES)
        cities = self.__sample_cities(config.CITIES)
        plz = self.__get_plz_ranges(config.PLZ)
        if self._upper:
            streets = map(self.__clean_string, streets)
        for i in range(len(self._customers)):
            customer = self._customers[i]
            street = streets[i]
            city = cities[i]
            zip_code = str(np.random.randint(plz[city][0], plz[city][1])).zfill(5)
            address = Address(firstname=customer.get_firstname(),
                              lastname=customer.get_lastname(),
                              street=street,
                              zip_code=zip_code,
                              city=city)
            customer.set_address(address)

    def __sample_street_names(self, street_names_file):
        names, frequencies = self.__load_name_frequencies(street_names_file)
        probabilities = frequencies / np.sum(frequencies)
        street_names = np.random.choice(names, self._num_customers, p=probabilities)
        house_numbers = map(abs, map(int, np.random.normal(1, 50, self._num_customers)))

        sampled_streets = [u'{} {}'.format(e1, e2) for e1, e2 in zip(street_names, house_numbers)]

        return sampled_streets

    def __sample_forenames(self, real_names_file, num_items):
        """
        sample first names

        :param real_names_file:
        :param num_items:
        :return:
        """
        names, frequencies = self.__load_name_frequencies(real_names_file)
        probabilities = frequencies / np.sum(frequencies)
        forenames = np.random.choice(names, num_items, p=probabilities)
        return list(forenames)

    def __sample_surnames(self, surname_file):
        """
        sample surnames

        :param surname_file:
        :return:
        """
        names, frequencies = self.__load_name_frequencies(surname_file)
        probabilities = frequencies / np.sum(frequencies)
        surnames = np.random.choice(names, self._num_customers, p=probabilities)
        return list(surnames)

    def __sample_cities(self, cities_file):
        """
        sample city names

        :param cities_file:
        :return:
        """
        names, frequencies = self.__load_name_frequencies(cities_file)
        probabilities = frequencies / np.sum(frequencies)
        cities = np.random.choice(names, self._num_customers, p=probabilities)
        return list(cities)

    def __get_plz_ranges(self, plz_file):
        """

        :param plz_file:
        :return:
        """
        plz_ranges = dict()
        cr = DictReader(open(plz_file, 'r'))
        for row in cr:
            plz_ranges[u'{}'.format(row['name'].decode('utf-8'))] = (int(row['start']), int(row['end']))
        return plz_ranges

    @staticmethod
    def __load_name_frequencies(frequency_file):
        """
        read actual names and their respective frequencies from csv file.
        Return list of names and list of frequencies.

        :param frequency_file: name of csv file
        :return: list of names, list of frequencies
        """
        names, frequencies = list(), list()
        cr = DictReader(open(frequency_file, 'r'))
        for row in cr:
            names.append(row['name'].decode('utf-8'))
            frequencies.append(float(row['frequency']))
        return names, frequencies

    def __load_articles(self):
        """
        returns dictionary with articles and their respective prices and probabilities

        :return: None
        """
        article_skus = self._distributions['cartItems.articleSimpleSKU'].keys()
        article_probabilities = self._distributions['cartItems.articleSimpleSKU'].values()

        prices_mean = self._distributions['cartItems.price']['mean']
        prices_std = self._distributions['cartItems.price']['std']
        prices = map(SampleDataGenerator.__sample_article_price, np.random.normal(prices_mean, prices_std, size=len(article_skus)))

        self._articles = {'article_skus': article_skus,
                          'article_probabilities': article_probabilities,
                          'prices': prices}

    @staticmethod
    def __sample_article_price(price):
        price = float(np.round(np.abs(price))/100.0)
        if price > 0.05:
            price -= 0.05
        return price

    def __create_orders(self, output):

        idcs = np.random.choice(range(len(self._customers)),
                                size=self._num_orders,
                                replace=(not self._customers_unique))
        with open(output, 'w') as f:
            for i in range(self._num_orders):
                # select customer
                customer = self._customers[idcs[i]]

                order = self.__create_order(customer)
                self._orders.append(order)

                # store/print orders
                json_str = json.dumps(order.json_encode(), sort_keys=True)
                f.write(json_str + '\n')

    def __create_order(self, customer):

        # sample solvency score
        solvency_score = float(np.random.normal(float(self._distributions['solvencyScore.score']['mean']),
                                                float(self._distributions['solvencyScore.score']['std'])))

        # sample number of iterations
        iteration = int(np.round(np.random.normal(float(self._distributions['iteration']['mean']),
                                                  float(self._distributions['iteration']['std']))))

        # sample open amount
        open_amount = np.abs(float(np.random.normal(float(self._distributions['openAmount']['mean']),
                                                    float(self._distributions['openAmount']['std'])))/100.0)

        # sample coupon code
        cc_prob = float(self._distributions['couponCode']['True'])
        coupon_code = np.random.choice([True, False], p=[cc_prob, 1-cc_prob])

        # sample label
        label = self.__sample_label()

        # increment global id
        SampleDataGenerator.id += 1

        # create new order
        order = Order(id=SampleDataGenerator.id,
                      customer=customer,
                      shipping_address=customer.get_address(),
                      billing_address=customer.get_address(),
                      solvency_score=solvency_score,
                      iteration=iteration,
                      open_amount=open_amount,
                      coupon_code=coupon_code,
                      label=label)

        # add cart items
        # sample open amount
        num_cart_items = int(np.abs(np.random.normal(float(self._distributions['numCartItems']['mean']),
                                                     float(self._distributions['numCartItems']['std']))))
        num_cart_items = max(1, num_cart_items)  # ensure that cart is not empty

        # sample articles
        article_idcs = np.random.choice(range(len(self._articles['article_skus'])),
                                        size=num_cart_items,
                                        p=self._articles['article_probabilities'])
        for i in article_idcs:
            article = Article(self._articles['article_skus'][i], self._articles['prices'][i])
            order.add_cart_item(article)

        if self._simple_mode:
            order = SimpleOrder(billing_address=customer.get_address())

        return order

    def __sample_label(self):
        """
        returns random label (True, False) according to fraud probability

        :return: bool
        """
        p_benign = 1.0 - self._fraud_probability
        return bool(np.random.choice([True, False], p=[self._fraud_probability, p_benign]))

    @staticmethod
    def __read_marginal_distributions(distr_file):
        """
        read marginal distributions from given CSV file.

        :param distr_file: csv file
        :return: 2-dimensional dictionary
        """
        d = defaultdict(dict)
        cr = DictReader(open(distr_file, 'r'))
        for row in cr:
            feature = row['feature']
            d[feature][row['realisation/statistic'].decode('utf-8')] = float(row['log_frequency/value'])
        return d

    def set_simple_mode(self, simple):
        """
        create orders only containing billing address

        :param simple: bool
        :return: None
        """
        self._simple_mode = simple

    def set_fraud_probability(self, fraud_probability):
        """
        set probability that generated order is labeled as fraud

        :param fraud_probability: float
        :return: None
        """
        self._fraud_probability = fraud_probability

    def set_unique_customers(self, unique_customers):
        """
        set whether customers are sampled without replacement,
        i.e. each customer gets assigned to only one order

        :param unique_customers: bool
        :return: None
        """
        if (unique_customers is True) and (self._num_customers < self._num_orders):
            err_msg = 'Number of customers should not be smaller than number of orders' \
                      'when using \'--unique_customers\' option.'
            raise Exception(err_msg)
        self._customers_unique = unique_customers

