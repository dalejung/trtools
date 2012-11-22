"""
    The apply_put functions create the output object first and then 
    fills in the data. This is to cut down on creating/merging many objects.  

    The main conceit is that the index of the output is the same. This allows us to preallocate 
    the output. 

    We also keep a single intermediary dataframe and re-use it for apply funcs. 

    We support dict of Series as output to cut down on intermediary DataFrame construction
    Which is only workable since we assume the indexes are the same. 
"""
import numpy as np
import pandas as pd
from pandas.core.groupby import DataFrameGroupBy, SeriesGroupBy, BinGrouper

import trtools.core.timeseries as ts # downsample moneky patch
from trtools.monkey import patch

def apply_put_series(data, grouper, func, *args, **kwargs):

    # grab first result to find dtype
    first = grouper.bins[0]
    res = func(data[0:first], *args, **kwargs)
    out = np.empty(len(data), dtype=res.dtype)  
    out[0:first] = res

    start = first
    for bin in grouper.bins[1:]:
        if start == bin:
            continue
        out[start:bin] = func(data[start:bin], *args, **kwargs)
        start = bin
    return pd.Series(out, index=data.index) 

def _empty_dataframe(data, res):
    """
        Handle creating out container for DataFrame-like output
    """
    out = {}
    for c in res:
        s = _empty_series(data, res[c])
        out[c] = s

    return out

def _empty_series(data, res):
    out = np.empty(len(data), dtype=res.dtype)  
    return out

def apply_result_series(out, res, start, end):
    out[start:end] = res.values

def apply_result_dict(out, res, start, end):
    """
        res can be both a dict or a DataFrame
        Returning a dict can speed up calculations quite a bit
    """
    for k in out.keys():
        out[k][start:end] = res[k]

def apply_put_frame(data, grouper, func, *args, **kwargs):
    # grab first result to find dtype
    first = grouper.bins[0]
    first_data = data[:first]
    res = func(first_data, *args, **kwargs)

    # assuming that res and data will share same index
    if isinstance(res, dict):
        out = _empty_dataframe(data, res)

    if isinstance(res, pd.DataFrame):
        out = _empty_dataframe(data, res)

    if isinstance(res, pd.Series):
        out = _empty_series(data, res)

    apply_result = apply_result_series
    if isinstance(out, dict):
        apply_result = apply_result_dict

    apply_result(out, res, 0, first)

    group = data.head() # reuse this dataframe below
    start = first
    for bin in grouper.bins[1:]:
        if start == bin:
            continue
        # HACK. Reuse the group dataframe and just replace it's block manager
        # must faster without creating new dataframes
        ds = data._data.get_slice(slice(start,bin), 1)
        group._data = ds
        group._clear_item_cache()

        res = func(group, *args, **kwargs)
        apply_result(out, res, start, bin)
        start = bin

    if isinstance(out, dict):
        return pd.DataFrame(out, index=data.index, columns=res.keys())

    if out.ndim > 1:
        return pd.DataFrame(out, index=data.index, columns=res.columns)
    else:
        return pd.Series(out, index=data.index)

def apply_put(data, grouper, func, *args, **kwargs):
    if isinstance(data, pd.Series):
        return apply_put_series(data, grouper, func, *args, **kwargs)

    if isinstance(data, pd.DataFrame):
        return apply_put_frame(data, grouper, func, *args, **kwargs)

@patch([SeriesGroupBy, DataFrameGroupBy], 'apply_put')
def apply_put_monkey(self, func, *args, **kwargs):
    grouper = self.grouper
    if not isinstance(grouper, BinGrouper):
        raise Exception("grouper must be BinGrouper")
    obj = self.obj
    return apply_put(obj, grouper, func, *args, **kwargs)

def s(df):
    h = pd.stats.moments.expanding_count(df.high)
    l = df.low.cumsum()
    return {'high':h, 'low':l}

if __name__ == '__main__':
    ind = pd.date_range(start="2000-01-01", freq="h", periods=1000000)
    df = pd.DataFrame({'high': 1.9, 'low':range(len(ind))}, index=ind)
    grouped = df.downsample('W')

    func = lambda df: pd.stats.moments.expanding_count(df.high)
    out = apply_put_frame(df, grouped.grouper, func)
