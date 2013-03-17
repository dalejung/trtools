"""
Purpose of this is to handle MultiIndexes and ObjectIndexes in a more convenient
manner. Much like how DatetimeIndex has convenience tools like df.index.hour == 3.

I want the equivalent for objects and multiindexes
"""
import itertools

import numpy as np
import pandas as pd

from trtools.monkey import patch_prop

class IndexGetter(object):
    def __init__(self, obj, attr=None):
        self._obj = obj
        if isinstance(obj, pd.Index) and attr is None:
            self._index = obj
        else:
            self._index = getattr(obj, attr)

    def __getattr__(self, name):
        if name in self.names:
            return self.sub_column(name)
        raise AttributeError(name)

    def sub_column(self, name):
        """
        Return the value of name for every item in obj.columns
        """
        raise NotImplementedError('Implement this in subclass')

    @property
    def names(self):
        raise NotImplementedError('Implement this in subclass')

class MultiIndexGetter(IndexGetter):
    """
    Handles MultiIndex. 
    Requires that that the levels be named.
    """
    def sub_column(self, name):
        return self._index.get_level_values(name)

    @property
    def names(self):
        """
        Complete based off of MultiIndex.names
        """
        return [c for c in self._index.names]

def _get_val(obj, name):
    if isinstance(obj, dict):
        return obj[name]
    return getattr(obj, name)

class ObjectIndexGetter(IndexGetter):
    """
    Handles an Index of objects and treats the attributes like un-ordered levels. 
    """
    def sub_column(self, name):
        return pd.Index([_get_val(col, name) for col in self._index])

    @property
    def names(self):
        """
        Try to grab the proper attrs for the Columns
        Best case is that the object has a keys method.
        """
        test = self._index[0]
        try:
            names = test.keys()
            return names
        except:
            names = test.__dict__.keys()
            return names

def _getter(obj, attr='columns'):
    if isinstance(obj.columns, pd.MultiIndex):
        return MultiIndexGetter(obj, attr=attr)

    test = obj.columns[0]
    if isinstance(obj.columns, pd.Index) and not np.isscalar(test):
        return ObjectIndexGetter(obj, attr=attr)

@patch_prop([pd.DataFrame], 'col')
def col(self):
    return _getter(self)

@patch_prop([pd.MultiIndex], 'lev')
def lev(self):
    return MultiIndexGetter(self)

# IPYTYHON
def install_ipython_completers():  # pragma: no cover
    """Register the DataFrame type with IPython's tab completion machinery, so
    that it knows about accessing column names as attributes."""
    from IPython.utils.generics import complete_object
    from pandas.util import py3compat

    @complete_object.when_type(MultiIndexGetter)
    def complete_column_panel_items(obj, prev_completions):
        return prev_completions + [c for c in obj.names \
                    if isinstance(c, basestring) and py3compat.isidentifier(c)]                                          

# Importing IPython brings in about 200 modules, so we want to avoid it unless
# we're in IPython (when those modules are loaded anyway).
import sys
if "IPython" in sys.modules:  # pragma: no cover
    try: 
        install_ipython_completers()
    except Exception:
        pass 
