import pandas as pd
import numpy as np

def searchsorted(self, *args, **kwargs):
    return np.searchsorted(self.values, *args, **kwargs)

if not hasattr(pd.Series, "searchsorted"):
    pd.Series.searchsorted = searchsorted
