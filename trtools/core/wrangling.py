from collections import OrderedDict

import pandas as pd
import numpy as np
from pandas import Panel, DataFrame, MultiIndex, Series

from trtools.monkey import patch

import trtools.core.timeseries as timeseries
from trtools.core.column_panel import PanelDict
import trtools.core.dataset as trdataset

@patch(Series, 'dropper')
def dropper(self, value=None, *args, **kwargs):
    if value is None:
        return self.dropna(*args, **kwargs)
    return self.ix[self != value].dropna()

@patch(DataFrame, 'dropper')
def dropna_df(self, value=None, *args, **kwargs):
    if value is None:
        return self.dropna(*args, **kwargs)
    return self.ix[self != value].dropna()

@patch([DataFrame, Series], 'reset_time')
def reset_time(self, *args, **kwargs):
    inplace = kwargs.pop('inplace', False)
    if not inplace:
        self = self.copy()
    return timeseries.reset_time(self, *args)

@patch(Panel, 'foreach')
def foreach_panel(self, func, *args, **kwargs):
    """
        Really just does a foreach with each being dfs in a panel. 
    """
    d = {}
    for key, df in self.iteritems():
        d[key] = func(df, *args, **kwargs)
    container = PanelDict
    for key, result in d.items():
        if isinstance(result, Series):
            container = DataFrame
        if isinstance(result, DataFrame):
            container = Panel
    return container(d)

@patch(DataFrame, 'foreach')
def foreach_dataframe(self, func, force_dict=False, *args, **kwargs):
    """
        Really just does a foreach with each being dfs in a panel. 
    """
    d = {}
    for key, df in self.iteritems():
        d[key] = func(df, *args, **kwargs)
    container = PanelDict
    for key, result in d.items():
        if isinstance(result, Series):
            container = DataFrame
            break
        if isinstance(result, DataFrame):
            container = Panel
            break

    index = []
    for key, result in d.items():
        if not isinstance(result, (DataFrame, Series)):
            continue
        result.name = key
        ind = result.index
        index = set(index).union(ind) 

    if force_dict:
        return PanelDict(d)

    res = DataFrame(None, index=index)
    for key, result in d.items():
        res = res.join(result)

    res = res.sort()
    return res

def _func_name(func):
    if isinstance(func, basestring):
        return func
    if callable(func):
        return func.func_name

def func_translate(name, obj):
    if hasattr(obj, name):
        func = lambda df: getattr(df, name)()
        return func

    bits = name.split('_')
    name = bits[0]
    if name == 'quantile':
        q = int(bits[1])
        q = q / 100.0
        return lambda df: getattr(df, name)(q)

@patch([Series, DataFrame], 'table')
def table_agg(self, funcs):
    """
        Good for summary statistics.

        >>> df.table(['mean', 'sum'])
        
        Will return a summary DataFrame like:
            'mean'   'sum'
       col1   2        200
       col2   3        300
    """
    # list of func names
    fdict = OrderedDict()
    if isinstance(funcs, list):
        for f in funcs:
            if isinstance(f, tuple):
                name, func = f
            else:
                name = _func_name(f)
                func = f
            fdict[name] = func

    data = OrderedDict()
    for k, f in fdict.items():
        func = f
        if isinstance(f, basestring):
            func = func_translate(f, self)
        else:
            func = lambda df: df.apply(f)

        res = func(self)
        data[k] = res

    res = pd.DataFrame(data, columns=data.keys()).T
    return res

@patch([DataFrame], 'pairwise')
def pairwise(self, func, force_values=True, order=True):
    """
        Basically a rip of DataFrame.corr
        func : callable
            will be passed in two Series 
            func(A,B) corresponds to return[A, B] of the return
            matrix. So A represents the index and B represents
            the column value
        force_values:
            will skip the autoboxing of Series and just send in
            the np.ndarray. Much faster.
        order:
            Does order matter? If no, then func(i,j) == func(j,i)

    Example usage would be calculating Sharpe Ratio when one asset is shorted
    and the other held long. In that case order would be True.
    """
    numeric_df = self._get_numeric_data()
    cols = numeric_df.columns
    K = len(cols)
    if force_values:
        # speed up. values sent to func will be np.ndarray
        numeric_df = numeric_df.values.T
    else:
        numeric_df.columns = range(K)

    matrix = np.empty((K,K), dtype=float)

    for i in range(K):
        A = numeric_df[i]
        start = i
        if order:
            start = 0
        for j in range(start, K):
            B = numeric_df[j]

            val = func(A, B)
            matrix[i, j] = val
            if not order:
                matrix[j, i] = val

    return self._constructor(matrix, index=cols.copy(), columns=cols.copy())

@patch(DataFrame, 'to_frame')
def df_to_frame(self):
    """
    """
    return self

def _dshift_fill_value(dtype):
    if dtype == bool:
        return False
    if dtype == int:
        return -1
    return np.nan

@patch(DataFrame, 'dshift', override=True)
def dshift(self, periods, fill_value=None, raw=False):
    """
    dtype-safe shift

    Basically a shift that preserves dtype by using a nan 
    sentinel value. 

    Parameters
    -----------
        periods : int
            akin to DataFrame.shift(periods)
        fill_value : scalar, optional
            Value to fill instead of NaN
        raw: boolean, default False
            If True, return the np.ndarray without wrapping.

    Default fill_value
    ------------------
    int : -1
    bool : False
    float : np.nan
    object : np.nan

    Use Case
    --------
    >>> bool_df = df > 0
    >>> %timeit bool_df.shift(1) | bool_df.shift(2) # slow due to object dtype
    1 loops, best of 3: 875 ms per loop
    >>> bool_df.dshift(1) | bool_df.dshift(2) # fast!
    100 loops, best of 3: 6.09 ms per loop
    """
    vals = self.values
    dtype = vals.dtype
    if fill_value is None:
        fill_value = _dshift_fill_value(dtype)

    shape = self.shape
    order = 'C'
    if vals.flags['F_CONTIGUOUS']:
        order = 'F'

    arr = np.ndarray(shape, dtype=dtype, order=order)
    arr[:] = fill_value

    arr_slice = slice(periods, shape[0])
    val_slice = slice(None, -periods)
    # re-arrange if period is negative
    if periods < 0:
        arr_slice = slice(None, periods)
        val_slice = slice(-periods, None)

    arr[arr_slice] = vals[val_slice]
    if raw:
        return arr
    return pd.DataFrame(arr, index=self.index, columns=self.columns)
