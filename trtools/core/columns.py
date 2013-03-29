"""
Purpose of this is to handle MultiIndexes and ObjectIndexes in a more convenient
manner. Much like how DatetimeIndex has convenience tools like df.index.hour == 3.

I want the equivalent for objects and multiindexes
"""
import itertools
import operator

import numpy as np
import pandas as pd
from pandas.util import py3compat

from trtools.monkey import patch_prop

def _sub_method(op, name):
    def _wrapper(self, other):
        if isinstance(other, LevelWrapper):
            other = other.values
        return op(self.values, other)
    return _wrapper

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

    def __array__(self):
        vals = self.values
        # vals is pd.Index
        # pd.Index promotes flaots to objects, we demote to float if it's numeric
        if vals.is_numeric() and not isinstance(vals, pd.Int64Index):
            vals = vals.values.astype(float)
        return vals

    #----------------------------------------------------------------------
    #   Arithmetic operators

    __add__ = _sub_method(operator.add, '__add__')
    __sub__ = _sub_method(operator.sub, '__sub__')
    __mul__ = _sub_method(operator.mul, '__mul__')
    __truediv__ = _sub_method(operator.truediv, '__truediv__')
    __floordiv__ = _sub_method(operator.floordiv, '__floordiv__')
    __pow__ = _sub_method(operator.pow, '__pow__')

    #__radd__ = _sub_method(_radd_compat, '__add__')
    __rmul__ = _sub_method(operator.mul, '__mul__')
    __rsub__ = _sub_method(lambda x, y: y - x, '__sub__')
    __rtruediv__ = _sub_method(lambda x, y: y / x, '__truediv__')
    __rfloordiv__ = _sub_method(lambda x, y: y // x, '__floordiv__')
    __rpow__ = _sub_method(lambda x, y: y ** x, '__pow__')

    # comparisons
    __gt__ = _sub_method(operator.gt, '__gt__')
    __ge__ = _sub_method(operator.ge, '__ge__')
    __lt__ = _sub_method(operator.lt, '__lt__')
    __le__ = _sub_method(operator.le, '__le__')
    __eq__ = _sub_method(operator.eq, '__eq__')
    __ne__ = _sub_method(operator.ne, '__ne__')

    # Python 2 division operators
    if not py3compat.PY3:
        __div__ = _sub_method(operator.div, '__div__')
        __rdiv__ = _sub_method(lambda x, y: y / x, '__div__')
        __idiv__ = __div__


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
