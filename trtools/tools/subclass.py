import collections
from operator import attrgetter

import pandas as pd
import numpy as np

from trtools.monkey import AttrProxy, AttrNameSpace

def wrap_methods(pandas_cls):
    """
        Take methods from pandas_cls and wrap so they return the proper class
        and metadata

        Wrap magic methods and grabs common methods from UserPandasObject
    """
    # transfer the  common PandasObject methods. Could be part of a meta class?
    # not sure how to ignore __class__ since it's callable. So explicitly ignoring it here
    ignore_list = ['__class__', '__metaclass__']

    # Wrap the magic_methods which won't be called via __getattribute__
    magic_methods = [(name, meth) for name, meth in pandas_cls.__dict__.items() \
                     if name.startswith('_') and isinstance(meth, collections.Callable) \
                    and name not in ignore_list and not isinstance(meth, type)]

    method_dict = {}
    for name, meth in magic_methods:
        method_dict[name] = _wrap_method(name)

    return method_dict

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

class MetaPandas(type):
    def __new__(cls, name, bases, dct):
        new_attrs = dct
        if '__pandas_cls__' in dct:
            pandas_cls = dct['__pandas_cls__']
            new_attrs = wrap_methods(pandas_cls)
            new_attrs.update(dct)

        # attach functions needed for subclassing to work
        meta_funcs = [(attr, meth) for attr, meth in list(cls.__dict__.items())
                      if not attr.startswith('__')]
        new_attrs.update(meta_funcs)
        return super(MetaPandas, cls).__new__(cls, name, bases, new_attrs)

    def _wrap(self, name):
        """
        """
        attr = self.pget(name)
        if isinstance(attr, collections.Callable):
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
        """
        attr = getattr(super(SubFrame, self), name)
        res = attr
        if isinstance(attr, collections.Callable):
            res = attr(*args, **kwargs)
        # maybe need better way to tell when to wrap?
        # do not wrap subclasses of UserFrame/UserSeries
        if isinstance(res, type(self).__pandas_cls__) and \
           not isinstance(res, (UserFrame)):
            res = type(self)(res)
            # transfer metadata
            d = self.__dict__
            new_dict = res.__dict__
            for k in list(d.keys()):
                if k in new_dict:
                    continue
                new_dict[k] = d[k]
        return res

