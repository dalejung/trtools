import collections

import numpy as np

from pandas import Panel, DataFrame, MultiIndex, Series, Timestamp
from pandas.core.indexing import _IXIndexer

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
        if not isinstance(key, tuple):
            key = (key,)

        if type(key) is tuple:
            try:
                return self.obj.get_value(*key)
            except Exception:
                pass

            info_axis_number = self.obj._info_axis_number
            if len(key)-1 >= info_axis_number:
                key = process_info_axis(self.obj, key)
            return ix._getitem_tuple(key)
        else:
            return ix._getitem_axis(key, axis=0)

    def __setitem__(self, key, value):
        self.obj._ix[key] = value

    def __getattr__(self, key):
        return getattr(self.obj._ix, key)

_is_bool = lambda x: isinstance(x, bool) or isinstance(x, np.bool_)
def process_info_axis(obj, key):
    """
    obj : NDFrame
    key : object/list
        Proper form is largely dependent on the KEY_TRANS

    Will translate keys for the info axis (DataFrame.columns, Panel.items) with
    the translate function.
    """
    # columns on DataFrame, items on Panel
    info_axis_number = obj._info_axis_number
    info_axis = obj._get_axis(info_axis_number)
    columns = key[info_axis_number]
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
        ind = info_axis.get_loc(columns)
        cols = info_axis[ind]
    else:
        columns = [KEY_TRANS.get(c, c) for c in columns]
        cols = [info_axis[info_axis.get_loc(c)] for c in columns]

    new_key = list(key)
    new_key[info_axis_number] = cols
    return tuple(new_key)

@patch_prop([DataFrame, Panel], 'ix')
def ix(self):
    """
    """
    if not hasattr(self, '_ix') or self._ix is None:
        self._ix = _IXIndexer(self, 'ix')

    if not hasattr(self, '_trx') or self._trx is None:
        self._trx = TransFrameIndexer(self)

    return self._trx
