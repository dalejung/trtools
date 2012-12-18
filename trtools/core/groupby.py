import collections

import numpy as np
import pandas as pd

from pandas import Panel, MultiIndex, Series
from pandas.core.groupby import DataFrameGroupBy, PanelGroupBy, BinGrouper

from trtools.monkey import patch, patch_prop
from trtools.core.column_panel import PanelDict

class PanelGroupByMap(object):
    """
        All DataFrame in a Panel share the same index. If you have a groupby
        that applies to all dataframes in a panel i.e. date groupings, then
        this method will reuse the grouper indices, saving you from re-running
        the groupby for each dataframe.
    """
    def __init__(self, groupby):
        self.groupby = groupby
        self.grouper = groupby.grouper
        self.obj = groupby.obj
        # create the first df groupby so we can delegate from __getattr__
        f_ind = groupby.obj.items[0]
        self.first = DataFrameGroupBy(groupby.obj.ix[f_ind], grouper=self.grouper)

    def __getattr__(self, attr):
        if hasattr(self.first, attr):
            return self._map_wrapper(attr)

    def _map_wrapper(self, attr):
        def mapper(*args, **kwargs):
            return self.apply(attr, *args, **kwargs)
        return mapper

    def apply(self, func, *args, **kwargs):
        result = {}
        for key, df in self.obj.iteritems():
            grp = DataFrameGroupBy(df, grouper=self.grouper)
            if not callable(func):
                f = getattr(grp, func)
                res = f(*args, **kwargs)
            result[key] = res
        return Panel.from_dict(result)


    def __call__(self, func, *args, **kwargs):
        """
            shortcut for agg. kept on forgetting that
            df_map.agg(lambda x: x) would work
        """
        args = list(args)
        args.insert(0, func)
        return self.apply('apply', *args, **kwargs)

@patch_prop([PanelGroupBy], 'df_map')
def df_map(self):
    return PanelGroupByMap(self)

@patch([PanelGroupBy, DataFrameGroupBy], 'foreach')
def foreach_panelgroupby(self, func, *args, **kwargs):
    """
        Will func the func for each group df for each item in panel.
    """
    keys = []
    values = []
    indices = self.grouper.indices

    if isinstance(self.obj, Panel):
        items = self.obj.iteritems()
    else:
        items = [(None, self.obj)]

    results = PanelDict()
    for key, df in items:
        sub_results = PanelDict()
        results[key] = sub_results
        for date, idx in indices.iteritems():
            sub_df = df.take(idx)
            res = func(df, sub_df)
            keys.append((key, date))
            values.append(res)

    if len(results) == 1:
        return results.values()[0]
    return results

def filter_by_grouped(grouped, by, obj=None):
    if obj is None:
        obj = grouped.obj

    index = by
    if isinstance(by, np.ndarray) and by.dtype == bool:
        index = by[by].index

    if isinstance(grouped.grouper, BinGrouper):
        return filter_bingroup_index(grouped, index, obj)
    return filter_grouper_index(grouped, index, obj)

def _reverse_flatten(mapping):
    rev_map = dict()
    for k, vals in mapping.iteritems():
        for v in vals:
            rev_map[v] = k

    return rev_map

# TODO These are mixed. bingroup returns the original obj sans the bad groups
# regular groupby returns a filtered groupby object
def filter_grouper_index(grouped, index, obj):

    old_groups = grouped.groups
    groups = {k:v for k, v in old_groups.iteritems() if k in index}
    rmap = _reverse_flatten(groups)

    return obj.groupby(rmap)

def filter_bingroup_index(grouped, index, obj):
    # http://stackoverflow.com/questions/13446480/python-pandas-remove-entries-based-on-the-number-of-occurrences
    # I think that overrides what i was doing...
    groups = list(_bingroup_groups(grouped))
    groups = collections.OrderedDict(groups)

    filtered_groups = [(i, groups[i]) for i in index]
    parts = []
    for i, slc in filtered_groups:
        # TODO: concat blocks instead of DataFrames, faster
        #bit = obj._data.get_slice(slice(slc[0], slc[1]), 1)
        bit = obj[slc[0]:slc[1]]
        parts.append(bit)

    res = pd.concat(parts)
    return res

def _bingroup_groups(grouped):
    grouper = grouped.grouper
    data = grouped.obj

    start = 0
    for edge, label in zip(grouper.bins, grouper.binlabels):
        yield label, (start, edge)
        start = edge

    if edge < len(data):
        yield grouper.binlabels[-1], (edge, len(data))

@patch([PanelGroupBy, DataFrameGroupBy], 'filter_grouped')
def filter_grouped_monkey(self, by):
    return filter_by_grouped(self, by)

@patch([PanelGroupBy, DataFrameGroupBy], 'process')
def panel_process(self, func):
    """
        Essentially just subsets the dataframe, runs func, and aggregates them back
    """
    import collections
    parts = collections.OrderedDict()

    grouped = self
    bins = grouped.grouper.bins
    binlabels = grouped.grouper.binlabels
    axis = self.axis
    start = 0
    for i, x in enumerate(bins):
        label = binlabels[i]
        sub = self.obj.ix._getitem_axis(slice(start, x), axis=axis)
        res = func(sub)
        parts[label] = res
        start = x

    return _wrap_parts(parts)

def _wrap_parts(parts):
    """
        parts should be a dict where the keys are the index
    """
    test = next(parts.itervalues())
    if np.isscalar(test):
        return pd.Series(parts)
    if isinstance(test, pd.Series):
        return pd.DataFrame(parts.values(), index=parts.keys())
    if isinstance(test, dict):
        # assumption is that dict is like a series
        res = pd.DataFrame(parts.values(), index=parts.keys())
        if isinstance(test, collections.OrderedDict):
            res = res.reindex(columns=test.keys())
        return res
    if isinstance(test, pd.DataFrame):
        return pd.Panel(parts).transpose(2, 0, 1)

    return parts


@patch([PanelGroupBy, DataFrameGroupBy], 'subset')
def subset(self, key):
    """
        Return the sub dataset that would have been sent to 
        apply funcs.
    """
    grouped = self
    bins = grouped.grouper.bins
    binlabels = grouped.grouper.binlabels
    loc = None
    try:
        loc = binlabels.get_loc(key)
    except:
        pass
    if loc is None:
        loc = key

    if loc == 0:
        start = 0
    else:
        start = bins[loc - 1]

    end = bins[loc]
    axis = self.axis
    return self.obj.ix._getitem_axis(slice(start, end), axis=axis)

if __name__ == '__main__':
    ind =  pd.date_range(start="1990-01-01", freq="H", periods=10000)
    df = pd.DataFrame({'high': range(len(ind)), 'open': np.random.randn(len(ind))}, index=ind)
    grouped = df.downsample('D', closed="left")
    pos = grouped['open'].mean() > 0
    res = filter_by_grouped(grouped, pos)
