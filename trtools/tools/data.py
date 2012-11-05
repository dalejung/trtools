import collections

import pandas as pd

def convert_item(obj):
    if not isinstance(obj, collections.Iterable):
        return obj
    if isinstance(obj, basestring):
        return obj

    try:
        return pd.Series(obj)
    except:
        pass

    return obj

class DataDict(object):
    def __init__(self, items=None):
        self.data = {}

        if items is None:
            items = {}
        self.update(items)

    def update(self, items):
        for k,v in items.iteritems():
            v = convert_item(v)
            self.data[k] = v

    def __getattr__(self, key):
        if key in self.data:
            return self.data[key]
        raise AttributeError()

    def __repr__(self):
        return "Keys :" + repr(self.data.keys())
