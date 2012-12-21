import collections
from operator import attrgetter

import pandas as pd
import numpy as np

from trtools.monkey import AttrProxy, AttrNameSpace

class UserPandasObject(object):
    """
        Base methods of a quasi pandas subclass. 

        The general idea is that all methods from this class will
        wrap the output into the same class and transfer metadata
    """
    def __init__(self, *args, **kwargs):
        # do not call super. Superfluous since we have the .df
        pass

    def _get(self, name):
        """ Get base attribute. Not pandas object """
        return object.__getattribute__(self, name)
    
    def __getattribute__(self, name):
        # so far these are the only base attribute I need
        if name in ['pobj', '_delegate', '_wrap', '_get', '__array_finalize__']:
            return object.__getattribute__(self, name)
        
        if hasattr(self.pobj, name):
            return self._wrap(name) 
        
        return object.__getattribute__(self, name) 

    def __setattr__(self, name, value):
        if name in self._get('__dict__'):
            return object.__setattr__(self, name, value)
        if hasattr(self.pobj, name):
            return object.__setattr__(self.pobj, name, value)
        return object.__setattr__(self, name, value)

    def __getattr__(self, name):
        # unset the inherited logic here. 
        raise AttributeError(name)
    
    def _wrap(self, name):
        """
        """
        getter = attrgetter(name)
        attr = getter(self.pobj)
        if callable(attr):
            def _wrapped(*args, **kwargs):
                return self._delegate(name, *args, **kwargs)
            return _wrapped
        elif isinstance(attr, AttrNameSpace):
            # Not sure when to call this other than check AttrNameSpace
            # note this won't catch the .str namepsace yet
            # also doesn't catch .ix
            return AttrProxy(name, self.pobj, lambda obj, full: self._wrap(full))
        else:
            return self._delegate(name)
        
    def _delegate(self, name, *args, **kwargs):
        """
            Delegate to Pandas Object and wrap output.
        """
        getter = attrgetter(name)
        attr = getter(self.pobj)
        res = attr
        if callable(attr):
            res = attr(*args, **kwargs) 
            
        # maybe need better way to tell when to wrap?    
        if isinstance(res, self._pandas_type):
            res = type(self)(res)
            # transfer metadata
            d = self._get('__dict__')
            new_dict = res._get('__dict__')
            for k in d.keys():
                # skip df
                if k == 'pobj':
                    continue
                new_dict[k] = d[k]
        return res

class UserFrame(pd.DataFrame):
    _pandas_type = pd.DataFrame
    pobj = None
    def __new__(cls, *args, **kwargs):
        pobj = cls._pandas_type(*args, **kwargs)
        instance = object.__new__(cls)
        instance.pobj = pobj
        return instance

class UserSeries(pd.Series):
    _pandas_type = pd.Series
    pobj = None
    def __new__(cls, *args, **kwargs):
        pobj = cls._pandas_type(*args, **kwargs)
        instance = pd.Series.__new__(cls)
        instance = instance.view(UserSeries)
        instance.pobj = pobj
        return instance

    def __array_finalize__(self, obj):
        pass

def wrap_methods(cls, pandas_cls):
    """
        Take methods from pandas_cls and wrap so they return the proper class
        and metadata

        Wrap magic methods and grabs common methods from UserPandasObject
    """
    user_methods = [(name, meth) for name, meth in UserPandasObject.__dict__.iteritems() \
                     if isinstance(meth, collections.Callable)]

    for name, meth in user_methods:
        setattr(cls, name, meth)

    magic_methods = [(name, meth) for name, meth in pandas_cls.__dict__.iteritems() \
                     if name.startswith('__') and isinstance(meth, collections.Callable)]
    for name, meth in magic_methods:
        if name in cls.__dict__:
            continue
        setattr(cls, name, _wrap_method(name))

    return magic_methods

def _wrap_method(name):
    def _meth(self, *args, **kwargs):
        return self._delegate(name, *args, **kwargs)
    return _meth

if __name__ == '__main__':
    wrap_methods(UserSeries, pd.Series)
    wrap_methods(UserFrame, pd.DataFrame)

    ind = pd.date_range(start="2000/1/1", freq="D", periods=1000)
    df = pd.DataFrame({'test': np.random.randn(len(ind)), 'bob': range(len(ind))}, index=ind)
    tf = UserFrame(df)
    s = UserSeries(df.test)
    tf + 1
    s + 1
