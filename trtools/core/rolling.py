import pandas as pd
import pandas.stats.moments as moments

from functools import partial

from trtools.monkey import attr_namespace

def wrap_rolling(func, obj):
    def wrapped(window, min_periods=None, freq=None):
        return pd.rolling_apply(obj, window, func, min_periods, freq=freq)
    return wrapped

@attr_namespace([pd.DataFrame, pd.Series], 'roll')
class Rolling(object):
    def attrs(self):
        """ default to pd.stats.moments """
        return moments.__all__

    def __getattr__(self, key):
        # default to base pandas moments
        if hasattr(moments, key):
            func = getattr(moments, key)
            return partial(func, self.obj)

        # support sum, mean as keys, still want to hit base pandas funcs
        if hasattr(moments, "rolling_"+key):
            func = getattr(moments, "rolling_"+key)
            return partial(func, self.obj)

        # try obj method i.e. df.prod
        if hasattr(self.obj, key):
            attr = getattr(self.obj, key)
            if callable(attr):
                func = lambda x: getattr(x, key)()
                return wrap_rolling(func, self.obj)

        raise AttributeError("No rolling func")
