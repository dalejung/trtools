from collections import OrderedDict
import numpy as np
from pandas import Series, Panel, DataFrame, Panel4D

from trtools.core.column_panel import ColumnPanel

def box_data(keys, data=None):
    """
    Box Data into appropiate pandas object

    Parameters
    ----------
    keys : dict or iterable
        Either keys list or Result Dict
    data : iterable
        list of data
    """
    if isinstance(keys, dict):
        rdict = keys
    else:
        rdict = OrderedDict(list(zip(keys, data)))

    test = next(iter(rdict.values()))
    if np.isscalar(test):
        return Series(rdict)

    if isinstance(test, Series):
        return DataFrame(rdict)

    if isinstance(test, DataFrame):
        return Panel(rdict)

    if isinstance(test, ColumnPanel):
        data = OrderedDict([(k, v.to_panel()) for k, v  in rdict.items()])
        return Panel4D(data)

    if isinstance(test, Panel):
        return Panel4D(data)

    return rdict
