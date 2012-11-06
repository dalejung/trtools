"""
    Collections of tools to quickly select rows/items
"""
import numpy as np

from pandas import Panel, DataFrame, MultiIndex, Series, Timestamp
from pandas.core.indexing import _NDFrameIndexer

from trtools.monkey import patch, patch_prop

@patch(DataFrame)
def cols(self, *args):
    return self.xs(list(args), axis=1)

@patch([DataFrame, Series])
def selectone(self, func):
    """
        A wrapper around select that only returns the first value
    """
    vals = self.select(func)
    if len(vals) > 0:
        return self.ix[vals.index[0]]

@patch(Series, 'show')
def show(self, val):
    """
        show(val)
        show all rows matching a value
        val can be a value or a func. 
    """
    if callable(val):
        func = np.vectorize(val)
        bools = func(self)
    else:
        bools = self == val
    return self[bools]

class PosIndexer(object):
    """
        Only indexes on int position. So if index is an IntIndex, it will never match
        the name. Only the position.
    """
    def __init__(self, obj):
        self.obj = obj
        self.get_func = self._set_get_item()

    def __getitem__(self, key):
        return self.get_func(key)

    def _set_get_item(self):
        if isinstance(self.obj, Panel):
            return self._getitem_panel
        if isinstance(self.obj, DataFrame):
            return self._getitem_dataframe
        if isinstance(self.obj, Series):
            return self._getitem_series

    def _getitem_panel(self, key):
        label = self.obj.major_axis[key]
        return self.obj.major_xs(label)

    def _getitem_dataframe(self, key):
        return self.obj.irow(key)

    def _getitem_series(self, key):
        label = self.obj.index[key]
        return self.obj[label]

@patch_prop([Panel, DataFrame, Series], 'rx')
def rx(self):
    """
        For grabbing row-wise which means the axis that a DatetimeIndex would 
        normally be found
    """
    if not hasattr(self, '_rx'):
        self._rx = PosIndexer(self)

    return self._rx

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
    cols = [col for col in obj.columns if col in key[1]]
    new_key.append(cols)
    new_key.extend(key[2:])
    return tuple(new_key)

@patch_prop([DataFrame], 'ix')
def ix(self):
    """
    """
    if not hasattr(self, '_ix') or self._ix is None:
        self._ix = _NDFrameIndexer(self)

    if not hasattr(self, '_trx') or self._trx is None:
        self._trx = TRFrameIndexer(self)

    return self._trx

@patch([DataFrame, Series])
def pluck(df, target, buffer=2):
    if not isinstance(target, int):
        try:
            target = df.index.get_loc(target)
        except:
            raise Exception("%s not in index" % target)
    lower = max(0, target - buffer)
    higher = min(len(df), target + buffer+1)
    return df.ix[lower:higher]

def time_pluck(df, target, buffer=2, index=None):
    from pandas.tseries.frequencies import to_offset
    """
        Instead of an pos-int pluck, we create a datetime-span 
    """
    if isinstance(buffer, int):
        buffer = "{0}D".format(buffer)

    offset = to_offset(buffer)

    start = Timestamp(target) - offset
    end = Timestamp(target) + offset
    if index is None:
        index = df.index

    filter = (index >= start) & (index <= end)
    return df.ix[filter]

# These patches are for supporting keys that are more meta objects than straight ints or strings
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


@patch([DataFrame], 'peek')
def peek(self, num_rows=5, max_col=None):
    # need to access the pandas column logic instead of hardcoded five
    max_col = max_col or 5
    max_col = self.columns.values[max_col]
    return self.ix[:num_rows, :max_col]

@patch([DataFrame], 'barf')
def barf(self, num_rows=5, max_col=None):
    """
        Keep on running into issues where in notebook, I want to just show everything.
    """
    from IPython.core.display import HTML
    import pandas.core.format as fmt 
    fmt.print_config.max_columns = 1000
    h = HTML(self.to_html())
    fmt.print_config.max_columns = None
    return h
