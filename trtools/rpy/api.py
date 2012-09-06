import pandas as pd
import pandas.rpy.common as rcom

import rpy2.robjects as robjects
from rpy2.robjects.vectors import SexpVector, ListVector, StrSexpVector
from trtools.monkey import patch, patch_prop
from rpy2.robjects.vectors import Vector

import trtools.rpy.conversion as rconv 
import trtools.rpy.tools as rtools
reload(rtools)
reload(rconv)

@patch([Vector], 'to_py')
def to_py(o):
    """
        Converts to python object if possible. 
        Otherwise wraps in ROBjectWrapper
    """
    res = None
    try:
        rcls = o.do_slot("class")
    except LookupError, le:
        rcls = []

    if isinstance(o, SexpVector) and len(rcls) > 0:
        if 'xts' in rcls:
            res = rconv.convert_xts_to_df(o)
        elif 'POSIXct' in rcls:
            res = rconv.convert_posixct_to_index(o)
        
        if res is None:
            res = robjects.default_ri2py(o)
            res = rtools.RObjectWrapper(res)

    if res is None:
        res = robjects.default_ri2py(o)

    return res

robjects.conversion.ri2py = robjects.default_ri2py

def pd_py2ri(o):
    """ 
    """
    res = None
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
