from trtools.monkey import AttrProxy, AttrNameSpace
from pandas_composition import *
import pandas_composition.base as base

def attrns_handler(self, name):
    return AttrProxy(name, self.pobj, lambda obj, full: self._wrap(full))

base.WRAP_HANDLERS.insert(0, (AttrNameSpace, attrns_handler))
