import pandas as pd
import pandas.rpy.common as rcom

import rpy2.robjects as robjects
from rpy2.robjects.vectors import SexpVector, ListVector, StrSexpVector

import trtools.rpy.conversion as rconv 
import trtools.rpy.tools as rtools
from trtools.rpy.rmodule import get_func, RPackage
import trtools.rpy.rplot as rplot

rplot.patch_call()

robjects.conversion.ri2py = robjects.default_ri2py


def pd_py2ri(o):
    """ 
    """
    res = None
    if isinstance(o, pd.Series): 
        o = pd.DataFrame(o, index=o.index)

    if isinstance(o, pd.DataFrame): 
        if isinstance(o.index, pd.DatetimeIndex):
            res = rconv.convert_df_to_xts(o)
        else:
            res = rcom.convert_to_r_dataframe(o)

    if isinstance(o, pd.DatetimeIndex): 
        res = rconv.convert_datetime_index(o)
        
    if res is None:
        res = robjects.default_py2ri(o)

    return res

robjects.conversion.py2ri = pd_py2ri

# easy access
r = robjects.r

def assign(name, obj):
    robjects.r.assign(name, obj)

# new r object.
class TrtoolsR(object):
    def __init__(self):
        pass

    def __getattr__(self, key):
        if hasattr(robjects.r, key):
            return getattr(robjects.r, key)
        raise AttributeError()

    def __call__(self, *args, **kwargs):
        return robjects.r(*args, **kwargs)

    def __getitem__(self, key):
        return robjects.r[key]

    def __setitem__(self, key, val):
        robjects.r.assign(key, val)

r = TrtoolsR()
