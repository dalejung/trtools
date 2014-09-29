import collections

import pandas as pd
import numpy as np

def convert_item(obj):
    if not isinstance(obj, collections.Iterable):
        return obj
    if isinstance(obj, str):
        return obj

    if isinstance(obj, (np.ndarray, pd.Series, pd.DataFrame, pd.Panel)):
        return obj

    try:
        return pd.Series(obj)
    except:
        pass

    return obj

class DataDict(object):
    def __init__(self, items=None):
        self._data = {}

        if items is None:
            items = {}
        self.update(items)

    def update(self, items):
        for k,v in items.items():
            v = convert_item(v)
            self._data[k] = v

    def __getattr__(self, key):
        if key in self._data:
            return self._data[key]
        raise AttributeError()

    def __repr__(self):
        return "Keys :" + repr(list(self._data.keys()))
