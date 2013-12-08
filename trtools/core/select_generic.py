"""
    The impedus of these patches was that I was using Objects as keys instead of strings. These
    objects both had an int-id and a string-id, and their comparison operators were overloaded
    ot support both types. The Object hashes were based off of the int-id.

    The default pandas stuff tends to check based off of hash(). So something like

    >>> aapl_stock == 'AAPL'  # TRUE
    >>> 'AAPL' in Index(aapl_stock) # FALSE

    note that

    >>> 'AAPL' in [aapl_stock]

    returns true since the list doesn't check based on id.

    This was a first pass attempt at rectifying the situation. Unfortunently, it's quite naive,
    does no caching, and can become a perf issue when doing many little slices.
"""
import collections

import numpy as np

from pandas import DataFrame
from pandas.core.indexing import _IXIndexer

from trtools.monkey import patch, patch_prop

class TRFrameIndexer(object):
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

            key = process_cols(self.obj, key)
            return ix._getitem_tuple(key)
        else:
            return ix._getitem_axis(key, axis=0)

    def __setitem__(self, key, value):
        self.obj._ix[key] = value

    def __getattr__(self, key):
        return getattr(self.obj._ix, key)

def process_cols(obj, key):
    """
        This is to support columns that are objects where the selection
        shouldn't be done by hash but by eq().

        This allows something like a Stock object to be used as a column
        and match both the ticker and an internal int id
    """
    if len(key) < 2:
        return key

    # pass through slice
    if isinstance(key[1], slice):
        return key


    new_key = [key[0]]
    cols = []
    # keep ordering
    columns = key[1]
    if not isinstance(columns, collections.Iterable) \
       or isinstance(columns, basestring):
        columns = [columns]

    for col in columns:
        for c in obj.columns:
            try:
                if c == col:
                    cols.append(c)
                    break
            except:
                pass

    # This means we did not match all cols. So we abort and run through regular
    # matching
    if len(cols) != len(columns):
        return key

    new_key.append(cols)
    new_key.extend(key[2:])
    return tuple(new_key)

# These patches are for supporting keys that are more meta objects than straight ints or strings
@patch_prop([DataFrame], 'ix')
def ix(self):
    """
    """
    if not hasattr(self, '_ix') or self._ix is None:
        self._ix = _IXIndexer(self)

    if not hasattr(self, '_trx') or self._trx is None:
        self._trx = TRFrameIndexer(self)

    return self._trx

@patch([DataFrame], '__getitem__')
def df__getitem__(self, key):
    """
        This is different because we are supporting objects as keys.
        Some keys might match both a basestring and int. The `in` keyword
        will match by hash so can only match one type.
    """
    try:
        columns = self.columns
        where = np.where(columns == key)[0]
        ind = where[0]
        key = columns[ind]
        col = self._old___getitem__(key)
        return col
    except:
        pass

    return self._old___getitem__(key)


@patch([DataFrame], '__getattr__')
def __getattr__(self, name):
    try:
        return self[name]
    except:
        pass

    return self._old___getattr__(name)
