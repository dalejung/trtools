from pandas import Panel, MultiIndex, Series
from pandas.core.groupby import DataFrameGroupBy, PanelGroupBy

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
        items = [(self.obj.name, self.obj)]

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
