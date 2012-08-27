from collections import OrderedDict

import numpy as np
import pandas as pd
from pandas.core.groupby import DataFrameGroupBy, SeriesGroupBy, BinGrouper


import trtools.core.timeseries as ts # downsample moneky patch
from trtools.monkey import patch, patch_prop

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

def apply_put_frame(data, grouper, func, *args, **kwargs):
    # call for all columns
    if callable(func):
        func = dict([(col, func) for col in data.columns])
             
    sdict = OrderedDict() 
    for col in data.columns:
        if col not in func:
            continue
        f = func[col]
        s = apply_put_series(data[col], grouper, f, *args, **kwargs)
        sdict[col] = s

    return pd.DataFrame(sdict, columns=sdict.keys(),index=data.index)

# TODO make a version that passes dataframe to func
def apply_put_frame2(data, grouper, func, *args, **kwargs):
    sdict = OrderedDict() 
    for col in data.columns:
        if col not in func:
            continue
        f = func[col]
        s = apply_put_series(data[col], grouper, f, *args, **kwargs)
        sdict[col] = s

    return pd.DataFrame(sdict, columns=sdict.keys(),index=data.index)

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
