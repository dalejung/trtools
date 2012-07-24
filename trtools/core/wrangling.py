from pandas import Panel, DataFrame, MultiIndex, Series

from trtools.monkey import patch

import trtools.core.timeseries as timeseries

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
def reset_time(self, *args):
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
