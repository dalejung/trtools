"""
Purpose of this is to handle MultiIndexes and ObjectIndexes in a more convenient
manner. Much like how DatetimeIndex has convenience tools like df.index.hour == 3.

I want the equivalent for objects and multiindexes
"""
import itertools
import operator

import numpy as np
import pandas as pd

from trtools.monkey import patch_prop

class LevelWrapper(object):
    def __init__(self, name, getter):
        self.name = name
        self.getter = getter

    def __getitem__(self, key):
        # get level value by .levels which are the distinct monotonic values
        if isinstance(key, int):
            return self.labels[key]
        raise KeyError(key)

    @property
    def labels(self):
        """
        Return the acutal labels. Equivalent of MultiIndex.levels[x]
        """
        return self.getter.level_name(self.name)

    @property
    def values(self):
        """ Returns the actual values """
        vals = self.getter.sub_column(self.name)
        return vals

    def level_op(self, other, op):
        return op(self.values, other)

    def __eq__(self, other):
        return self.level_op(other, operator.eq)

    def __ne__(self, other):
        return self.level_op(other, operator.ne)

    def __gt__(self, other):
        return self.level_op(other, operator.gt)

    def __ge__(self, other):
        return self.level_op(other, operator.ge)

    def __lt__(self, other):
        return self.level_op(other, operator.lt)

    def __le__(self, other):
        return self.level_op(other, operator.le)


class IndexGetter(object):
    def __init__(self, obj, attr=None):
        self._obj = obj
        if isinstance(obj, pd.Index) and attr is None:
            self._index = obj
        else:
            self._index = getattr(obj, attr)

    def __getattr__(self, name):
        if name in self.names:
            return LevelWrapper(name, self)
        raise AttributeError(name)

    def sub_column(self, name):
        """
        Return the value of name for every item in obj.columns
        """
        raise NotImplementedError('Implement this in subclass')

    @property
    def names(self):
        raise NotImplementedError('Implement this in subclass')

    def level_name(self, name):
        raise NotImplementedError('Implement this in subclass')

class MultiIndexGetter(IndexGetter):
    """
    Handles MultiIndex. 
    Requires that that the levels be named.
    """
    def sub_column(self, name):
        return self._index.get_level_values(name)

    def level_name(self, name):
        """
        Get the .levels value by name
        """
        ind = self._index.names.index(name)
        return self._index.levels[ind]

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

    def level_name(self, name):
        """
        Note that the only way to get the equivalent of MultiIndex.levels is to get all 
        values and then run unique. There should be caching done somewhere here
        """
        vals = self.sub_column(name)
        ind = vals.unique()
        ind.sort()
        ind = pd.Index(ind)
        return ind

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
    """
    This function returns IndexGetter based on obj and attr.
    In retrospect, this is a bit cludgy. It was done to support passing in 
    an object and not just its index.
    """
    index = getattr(obj, attr)
    getter_class = _getter_class(index)
    return getter_class(obj, attr=attr)

def _getter_class(index):
    """
    Parameters:
    ----------
        index : pd.Index
    Return:
    -------
        Proper IndexGetter class
    """
    if isinstance(index, pd.MultiIndex):
        return MultiIndexGetter

    test = index[0]
    if isinstance(index, pd.Index) and not np.isscalar(test):
        return ObjectIndexGetter

@patch_prop([pd.DataFrame], 'col')
def col(self):
    return _getter(self)

@patch_prop([pd.Index], 'lev')
def lev(self):
    return _getter_class(self)(self)

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
