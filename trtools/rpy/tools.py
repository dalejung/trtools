from collections import OrderedDict

from rpy2.rinterface import SexpVector, RNULLType, NULL
from rpy2.robjects.vectors import Vector, Matrix, DataFrame, ListVector, StrVector
import rpy2.robjects as robjects

import pandas.rpy.common as rcommon
import pandas as pd

from trtools.monkey import patch
import trtools.rpy.conversion as rconv 

def is_null(obj):
    return isinstance(obj, RNULLType)

def rinfo(obj):
    info = OrderedDict()
    try:
        info['classes'] = list(obj.rclass)
        if hasattr(obj, 'names') and not is_null(obj.names):
            info['names'] = list(obj.names)
        if hasattr(obj, 'list_attrs') and not is_null(obj.names):
            info['list_attrs'] = list(obj.list_attrs())
    except:
        pass
        
    return info    

def rrepr(obj):
    info = rinfo(obj)
    out = "" 
    for k,vals in info.iteritems():
        out += k + "\n"
        out += "\n".join(["\t"+str(val) for val in vals if val])
        out += "\n"
    return out 

def printr(obj):
    print rrepr(obj)

class RObjectWrapper(object):
    """
        Essentially a class with slightly better repr and easy access to
        attr, names, and slots
    """
    def __init__(self, robj):
        self.robj = robj

    def __repr__(self):
        out = "RObjectWrapper: {0}".format(type(self.robj))
        details = rrepr(self.robj)
        return out + details

    def __getattr__(self, name):
        """
            AFAIK, this should be fine as long as there are no name
            clashes. Haven't run into any.
        """
        obj = None
        if name in self.robj.names:
            obj = self.robj.rx2(name)
        if name in self.robj.list_attrs():
            obj = self.robj.do_slot(name)
        if hasattr(self.robj, name):
            obj = getattr(self.robj, name)

        # wrap attribute. 
        if obj is not None: 
            return obj.to_py()
    
        raise AttributeError()

def _repr(obj):
    if isinstance(obj, ListVector):
        if isinstance(obj.names, RNULLType):
            return "[{0} items]".format(len(obj))
        else:
            return "{" + ", ".join(obj.names) + '}'

    if isinstance(obj, basestring):
        return obj

    if isinstance(obj, (int, float)):
        return obj

    if isinstance(obj, StrVector) and len(obj) == 1:
        return obj[0]

    strr = str(obj)
    if len(strr) < 20:
        return strr.strip()
    
    return type(obj)


class RList(object):
    def __init__(self, data, robj):
        self.data = data
        self.robj = robj

    def __repr__(self):
        if isinstance(self.data, list):
            return self._repr_list()
        s = "{0}:\n{1}"
        lines = [s.format(name, _repr(val)) for name, val in self.data.items()]
        return "\n\n".join(lines)

    def _repr_list(self):
        lines = [_repr(val) for val in self.data]
        return '['+",\n".join(lines)+']'

    def __getattr__(self, key):
        if key in self.data:
            return self.data[key].to_py()
        raise AttributeError()

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        raise AttributeError()

def convert_ListVector(lt):
    data = {}
    for k, v in lt.iteritems():
        try:
            pass
            #v = to_py(v, skip_list=True)
        except:
            pass

        if k is None:
            data.setdefault(None, []).append(v)
        else:
            data[k] = v

    if len(data) == 1 and None in data:
        data = data[None]
    return RList(data, lt)

@patch([Vector], 'to_py')
def to_py(o, skip_list=False):
    """
        Converts to python object if possible. 
        Otherwise wraps in ROBjectWrapper
    """
    print repr(o)
    res = None
    try:
        rcls = o.do_slot("class")
        rcls = list(rcls)
    except LookupError, le:
        rcls = []

    try:
        rclass = list(o.rclass)
    except:
        rclass = []


    classes = rclass + rcls

    if isinstance(o, SexpVector) and len(classes) > 0:
        if 'xts' in classes:
            res = rconv.convert_xts_to_df(o)
        elif 'POSIXct' in classes:
            res = rconv.convert_posixct_to_index(o)
        elif 'logical' in classes:
            res = rcommon._convert_vector(o)

    if isinstance(o, ListVector) and not skip_list:
        res = convert_ListVector(o)

    if res is None:
        try:
            res = rcommon.convert_robj(o) # fallback to pandas
        except:
            pass

    try: 
        if len(res) == 1:
            return res[0]
    except:
        pass
        
    if res is None and isinstance(o, SexpVector):
        res = RObjectWrapper(o)

    if res is None:
        res = o

    return res

def simple_string_vector_repr(self):
    if len(self) == 1:
        return self[0]
    return SexpVector.__old_repr__(self)
