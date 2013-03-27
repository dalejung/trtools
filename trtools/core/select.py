"""
    Collections of tools to quickly select rows/items
"""
import collections

import numpy as np

from pandas import Panel, DataFrame, MultiIndex, Series, Timestamp
from pandas.core.indexing import _NDFrameIndexer

from trtools.monkey import patch, patch_prop

@patch(DataFrame, 'cols')
def _cols(self, *args):
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

@patch([DataFrame], 'peek')
def peek(self, num_rows=5, max_col=None):
    # need to access the pandas column logic instead of hardcoded five
    max_col = max_col or 5
    rows, cols = self.shape
    num_rows = min(num_rows, rows)
    max_col = min(max_col, cols)
    return self.iloc[:num_rows, :max_col]

@patch([DataFrame], 'barf')
def barf(self, num_rows=5, max_col=None):
    """
        Keep on running into issues where in notebook, I want to just show everything.
    """
    from IPython.core.display import HTML
    import pandas.core.config as config 
    config.set_option("print.max_columns", 1000)
    h = HTML(self.to_html())
    config.reset_option("print.max_columns")
    return h
