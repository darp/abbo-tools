

class Order(object):

    def __init__(self, id, customer, shipping_address, billing_address,
                 solvency_score, iteration, open_amount, coupon_code, label):
        super(Order, self).__init__()
        self.__id = id
        self.__cart_items = list()
        self.customer = customer
        self.shipping_address = shipping_address
        self.billing_address = billing_address
        self.solvency_score = solvency_score
        self.iteration = iteration
        self.open_amount = open_amount
        self.coupon_code = coupon_code
        self.label = label

    def add_cart_item(self, article):
        self.__cart_items.append(article)
        
    @property
    def grand_total(self):
        grand_total = 0.0
        for item in self.__cart_items:
            grand_total += item.price
        return grand_total

    def json_encode(self, keys=None):
        d = {'id': self.__id,
             'customer': self.customer.json_encode(),
             'shippingAddress': self.shipping_address.json_encode(),
             'billingAddress': self.billing_address.json_encode(),
             'cartItems': [e.json_encode() for e in self.__cart_items],
             'grandTotal': '{:.2f}'.format(self.grand_total),
             'solvencyScore': {'score': int(self.solvency_score)},
             'iteration': self.iteration,
             'openAmount': '{:.2f}'.format(self.open_amount),
             'couponCode': 'coupon_code' if self.coupon_code else '',
             'invoiceFraudLabel': self.label}
        ret_dict = dict()
        if keys is not None:
            for k in keys:
                if k in d:
                    ret_dict[k] = d[k]
        else:
            ret_dict = d
        return ret_dict


class SimpleOrder(Order):

    def __init__(self, billing_address):
        super(Order, self).__init__()
        self.billing_address = billing_address

    def json_encode(self, keys=None):
        d = {'billingAddress': self.billing_address.json_encode()}
        ret_dict = dict()
        if keys is not None:
            for k in keys:
                if k in d:
                    ret_dict[k] = d[k]
        else:
            ret_dict = d
        return ret_dict


class Customer(object):

    def __init__(self, firstname, lastname, email, gender):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.gender = gender
        self.address = None

    def get_firstname(self):
        return self.firstname

    def get_lastname(self):
        return self.lastname

    def set_address(self, address):
        self.address = address

    def set_email(self, email):
        self.email = email

    def get_address(self):
        return self.address

    def json_encode(self):
        return {'firstName': self.firstname,
                'lastName': self.lastname,
                'email': self.email,
                'gender': self.gender}


class Article(object):

    def __init__(self, article_sku, price):
        self.article_sku = article_sku
        self.price = price

    def json_encode(self):
        return {'articleSimpleSKU': self.article_sku,
                'price': '{:.2f}'.format(self.price)}


class Address(object):

    def __init__(self, firstname, lastname, street, zip_code, city=None):
        self.firstname = firstname
        self.lastname = lastname
        self.street = street
        self.zip_code = zip_code
        self.city = city

    def json_encode(self):
        return {'firstName': self.firstname,
                'lastName': self.lastname,
                'street': self.street,
                'zip': self.zip_code,
                'city': self.city}


def nested_objects_to_json(obj):
    if hasattr(obj, 'json_encode'):
        return obj.json_encode()
    else:
        raise TypeError('Object of type {} with value {} is not JSON serializable.'
                        .format(type(obj), repr(obj)))
