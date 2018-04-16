#!/usr/bin/env python
import sys
import simplejson as json
import random

articles = [
    {"articleSimpleSKU": "ALDA2H00N-K11", "price": "199.95"},
    {"articleSimpleSKU": "PAX44E019-Q11", "price": "99.95"}
]
shippingAddresses = [
    {"city": "Berlin", "firstName": "Donald", "lastName": "Drum", "street": "Spreeweg 1A", "zip": "10557"},
    {"city": "Berlin", "firstName": "Ronald", "lastName": "Drumbf", "street": "Spreeweg 1B", "zip": "10557"},
    {"city": "Berlin", "firstName": "John", "lastName": "Drumpf", "street": "Spreeweg 1C", "zip": "10575"}
]
solvencyScore = {"score": 0}

orders_file = sys.argv[1]
with open(orders_file, 'r') as f:
    for line in f:
        json_obj = json.loads(line)
        json_obj['cartItems'] = [articles[random.randint(0,len(articles)-1)]]
        json_obj['shippingAddress'] = shippingAddresses[random.randint(0, len(shippingAddresses)-1)]
        json_obj['solvencyScore'] = {"score":0}
        json_obj['invoiceFraudLabel'] = True
        print(json.dumps(json_obj))
