"""
Purpose of this is to handle MultiIndexes and ObjectIndexes in a more convenient
manner. Much like how DatetimeIndex has convenience tools like df.index.hour == 3.

I want the equivalent for objects and multiindexes
"""
import itertools

import numpy as np
import pandas as pd

from trtools.monkey import patch_prop

class MultiIndexGetter(object):
    def __init__(self, obj, attr='columns'):
        self._obj = obj
        self._index = getattr(obj, attr)

    def __getattr__(self, name):
        if name in self._index.names:
            return self._index.get_level_values(name)
        raise AttributeError()

def _getter(obj):
    if isinstance(obj.columns, pd.MultiIndex):
        return MultiIndexGetter(obj)

@patch_prop([pd.DataFrame], 'col')
def col(self):
    return _getter(self)

# IPYTYHON
def install_ipython_completers():  # pragma: no cover
    """Register the DataFrame type with IPython's tab completion machinery, so
    that it knows about accessing column names as attributes."""
    from IPython.utils.generics import complete_object
    from pandas.util import py3compat

    @complete_object.when_type(MultiIndexGetter)
    def complete_column_panel_items(obj, prev_completions):
        return prev_completions + [c for c in obj._index.names \
                    if isinstance(c, basestring) and py3compat.isidentifier(c)]                                          

# Importing IPython brings in about 200 modules, so we want to avoid it unless
# we're in IPython (when those modules are loaded anyway).
import sys
if "IPython" in sys.modules:  # pragma: no cover
    try: 
        install_ipython_completers()
    except Exception:
        pass 
