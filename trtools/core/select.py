"""
    Collections of tools to quickly select rows/items
"""
import collections
import warnings

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

@patch_prop([Panel, DataFrame, Series], 'rx')
def rx(self):
    """
        For grabbing row-wise which means the axis that a DatetimeIndex would 
        normally be found
    """
    warnings.warn(".rx is deprecated in favor of .iloc")
    return self.iloc

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

@patch([DataFrame], 'subset')
def subset(self, start, max=10):
    """
    Select a window of data.
    """
    if start < 0:
        start = len(self) + start
    end = start + max
    return self.ix[start:end]

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
    config.set_option("display.max_columns", 1000)
    h = HTML(self.to_html())
    config.reset_option("display.max_columns")
    return h
