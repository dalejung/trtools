import pandas as pd
import numpy as np

import pandas.core.common as com

def where(ser, cond, other=np.nan, inplace=False):
    """
    Analagous to Series.where, DataFrame.where.
    Also works with np.ndarray
    """
    if hasattr(ser, 'where'):
        return getattr(ser, 'where')(cond, other)

    ser = ser if inplace else ser.copy()

    if np.isscalar(other):
        other = np.array([other])

    if len(other) != len(ser):
        if len(other) == 1:
            other = np.array(other[0]*len(ser))

    change = ser 
    com._maybe_upcast_putmask(ser,~cond,other,change=change)

    return None if inplace else ser

isnull = pd.isnull
