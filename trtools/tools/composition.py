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

    def __setattr__(self, name, value):
        if name in self._get('__dict__'):
            return object.__setattr__(self, name, value)
        if hasattr(self.pobj, name):
            return object.__setattr__(self.pobj, name, value)
        return object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        if hasattr(self, name):
            return getattr(self, name)
        return object.__getattribute__(self, name)

    def __getattr__(self, name):
        # unset the inherited logic here. 
        if hasattr(self.pobj, name):
            return self._wrap(name)
        raise AttributeError(name)

    def __tr_getattr__(self, name):
        """
            Use this function to override getattr for subclasses

            This is necessary since we're subclassing pd.DataFrame as
            a hack. We can't use getattr since it'll return DataFrame attrs
            which we only use through the _wrap/delegate
        """
        raise AttributeError(name)

    def pget(self, name):
        """
            Shortcut to grab from pandas object
            Really just here to override on custom classes.
        """
        getter = attrgetter(name)
        attr = getter(self.pobj)
        return attr
    
    def _wrap(self, name):
        """
        """
        attr = self.pget(name)
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
        attr = self.pget(name)
        res = attr
        if callable(attr):
            res = attr(*args, **kwargs) 

        # maybe need better way to tell when to wrap?    
        # do not wrap subclasses of UserFrame/UserSeries
        if isinstance(res, type(self)._pandas_type) and \
           not isinstance(res, (UserFrame, UserSeries)):
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

class PandasMeta(type):
    def __new__(cls, name, bases, dct):
        new_attrs = dct
        # override the UserFrame/UserSeries
        if '_pandas_type' in dct:
            pandas_cls = dct['_pandas_type']
            new_attrs = get_methods(pandas_cls)
            new_attrs.update(dct)
        else: # should be subclass of UserFrame/UserSeries
            pass

        return super(PandasMeta, cls).__new__(cls, name, bases, new_attrs)

def get_methods(pandas_cls):
    """
        Get a combination of PandasObject methods and wrapped DataFrame/Series magic
        methods to use in MetaClass
    """
    ignore_list = ['__class__', '__metaclass__', '__dict__', '__new__', '__array_finalize__']
    methods = {}
    user_methods = [(name, meth) for name, meth in UserPandasObject.__dict__.iteritems() \
                     if isinstance(meth, collections.Callable) and name not in ignore_list]

    for name, meth in user_methods:
        methods[name] = meth

    # Wrap the magic_methods which won't be called via __getattribute__
    magic_methods = [(name, meth) for name, meth in pandas_cls.__dict__.iteritems() \
                     if name not in ignore_list]

    for name, meth in magic_methods:
        if name in methods: # don't override PandasObject methods
            continue

        if callable(meth):
            methods[name] = _wrap_method(name)
        else:
            methods[name] = _wrap_attr(name)

    return methods

def _prop(name):
    def _func(self):
        return self._wrap(name)
    return _func

def _wrap_attr(name):
    attr = property(_prop(name))
    return attr

def _wrap_method(name):
    def _meth(self, *args, **kwargs):
        return self._delegate(name, *args, **kwargs)
    return _meth

class UserFrame(pd.DataFrame):
    _pandas_type = pd.DataFrame
    pobj = None
    __metaclass__ = PandasMeta
    def __new__(cls, *args, **kwargs):
        pobj = cls._pandas_type(*args, **kwargs)
        instance = object.__new__(cls)
        instance.pobj = pobj
        return instance

class UserSeries(pd.Series):
    _pandas_type = pd.Series
    pobj = None
    __metaclass__ = PandasMeta

    def __new__(cls, *args, **kwargs):
        instance = pd.Series.__new__(cls, *args, **kwargs)
        return instance.view(cls)

    def __array_finalize__(self, obj):
        if isinstance(obj, UserSeries):
            self.pobj = obj.pobj
            return

        if isinstance(obj, pd.Series):
            self.pobj = obj
            return

        if isinstance(obj, np.ndarray):
            obj = pd.Series(obj)
            self.pobj = obj
            return

us = UserSeries(range(10))
s = us.view(UserSeries)
