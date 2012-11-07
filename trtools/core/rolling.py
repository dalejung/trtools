import pandas as pd
import pandas.stats.moments as moments

from functools import partial

from trtools.monkey import patch_prop

def wrap_rolling(obj, func):
    def wrapped(window, min_periods=None, freq=None):
        return pd.rolling_apply(obj, window, func, min_periods, freq=freq)

    return wrapped


class Rolling(object):
    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, key):
        # default to base pandas moments
        if hasattr(moments, "rolling_"+key):
            func = getattr(moments, "rolling_"+key)
            return partial(func, self.obj)

        # try obj method
        if hasattr(self.obj, key):
            attr = getattr(self.obj, key)
            if callable(attr):
                func = lambda x: getattr(x, key)()
                return wrap_rolling(self.obj, func)

        raise AttributeError("No rolling func")

@patch_prop([pd.DataFrame, pd.Series], 'rolling')
def rolling(self):
    """
    """
    if not hasattr(self, '_rolling') or self._rolling is None:
        self._rolling = Rolling(self)

    return self._rolling
