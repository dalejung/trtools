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
        """
            #NOTE The reason we use __getattribute__ is that we're
            subclassing pd.DataFrame. That means that our SubClass instance
            will have DataFrame methods that will be called on itself and 
            *not* the self.pobj. 

            This is confusing but in essense, UserFrame's self is an empty DataFrame.
            So calling its methods would operate on an empty DataFrame. We want
            to call the methods on pobj, which is where the data lives. 

            We will subclass the DataFrame to trick internal pandas machinery
            into thinking this class quacks like a duck.
        """
        # special attribute that need to go straight to this obj
        if name in ['pget', 'pobj', '_delegate', '_wrap', '_get', 
                    '__class__', '__array_finalize__', 'view', '__tr_getattr__']:
            return object.__getattribute__(self, name)

        try:
            return self.__tr_getattr__(name)
        except:
            pass

        # this is support inheritance for subclasses of UserFrame/UserSeries
        # for now it only supports the immediate
        type_dict = type(self).__dict__
        if '_pandas_type' not in type_dict and name in type_dict:
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
    ignore_list = ['__class__', '__metaclass__']
    methods = {}
    user_methods = [(name, meth) for name, meth in UserPandasObject.__dict__.iteritems() \
                     if isinstance(meth, collections.Callable) and name not in ignore_list]

    for name, meth in user_methods:
        methods[name] = meth

    # Wrap the magic_methods which won't be called via __getattribute__
    magic_methods = [(name, meth) for name, meth in pandas_cls.__dict__.iteritems() \
                     if name.startswith('_') and isinstance(meth, collections.Callable) \
                    and name not in ignore_list]

    for name, meth in magic_methods:
        if name not in methods: # don't override PandasObject methods
            methods[name] = _wrap_method(name)

    return methods

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
        # since i am not calling npndarray.__new__, UserSeries.__array_finalize__ 
        # does not get called.
        pobj = cls._pandas_type(*args, **kwargs)
        instance = pobj.view(cls)
        return instance

    def __array_finalize__(self, obj):
        if isinstance(obj, UserSeries):
            # self.values will be correct, but we don't have the index
            # TODO go over this logic again. it works but uh
            # not too happy about it
            object.__setattr__(self, '_index', obj._index)
            self.pobj = self.view(pd.Series)
            return

        if isinstance(obj, pd.Series):
            self.pobj = obj
            return

        if isinstance(obj, np.ndarray):
            obj = pd.Series(obj)
            self.pobj = obj
            return

        assert False
