import collections

import numpy as np

from pandas import Panel, DataFrame, MultiIndex, Series, Timestamp
from pandas.core.indexing import _NDFrameIndexer

from trtools.monkey import patch, patch_prop

KEY_TRANS = {}

@patch([DataFrame], '__getitem__', override=True)
def df__getitem__(self, key):
    """
        This is different because we are supporting objects as keys. 
        Some keys might match both a basestring and int. The `in` keyword
        will match by hash so can only match one type.
    """
    # Logic is to keep supporting strings even if they have an 
    # entry in translate table
    # Not sure if supporting ints is worthwhile since
    # int columns can exist automatically
    if isinstance(key, basestring) and key in self.columns:
        return self._old___getitem__(key) 

    try:
        key = KEY_TRANS.get(key, key)
        col = self._old___getitem__(key) 
        return col
    except:
        pass

    return self._old___getitem__(key) 

class TransFrameIndexer(object):
    """
        Taking over .ix
    """
    def __init__(self, obj):
        self.obj = obj

    def __getitem__(self, key):
        ix = self.obj._ix
        if type(key) is tuple:
            try:
                return self.obj.get_value(*key)
            except Exception:
                pass

            if len(key) >= 2:
                key = process_cols(self.obj, key)
            return ix._getitem_tuple(key)
        else:
            return ix._getitem_axis(key, axis=0)

    def __setitem__(self, key, value):
        self.obj._ix[key] = value

    def __getattr__(self, key):
        return getattr(self.obj._ix, key)

_is_bool = lambda x: isinstance(x, bool) or isinstance(x, np.bool_)
def process_cols(obj, key):
    """
    """

    columns = key[1]
    # don't handle slice columns
    if isinstance(columns, slice):
        return key

    # don't handle bool indexes
    if isinstance(columns, collections.Iterable) and _is_bool(columns[0]):
        return key

    cols = []

    # single key
    if not isinstance(columns, collections.Iterable) \
       or isinstance(columns, basestring):
        columns = KEY_TRANS.get(columns, columns)
        ind = obj.columns.get_loc(columns)
        cols = obj.columns[ind]
    else:
        columns = [KEY_TRANS.get(c, c) for c in columns]
        cols = [obj.columns[obj.columns.get_loc(c)] for c in columns]

    new_key = [key[0]]
    new_key.append(cols)
    new_key.extend(key[2:])
    return tuple(new_key)

@patch_prop([DataFrame], 'ix')
def ix(self):
    """
    """
    if not hasattr(self, '_ix') or self._ix is None:
        self._ix = _NDFrameIndexer(self, 'ix')

    if not hasattr(self, '_trx') or self._trx is None:
        self._trx = TransFrameIndexer(self)

    return self._trx
