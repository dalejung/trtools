from collections import OrderedDict
from rpy2.rinterface import SexpVector

def rinfo(obj):
    info = OrderedDict()
    info['classes'] = list(obj.rclass)
    if hasattr(obj, 'names'):
        info['names'] = list(obj.names)
    if hasattr(obj, 'list_attrs'):
        info['list_attrs'] = list(obj.list_attrs())
        
    return info    

def rrepr(obj):
    print type(obj)
    info = rinfo(obj)
    out = "" 
    for k,vals in info.iteritems():
        out += k + "\n"
        out += "\n".join(["\t"+val for val in vals])
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
        return rrepr(self.robj)

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
            if isinstance(obj, SexpVector):
                return RObjectWrapper(obj)
            else:
                return obj
    
        raise AttributeError()

def simple_string_vector_repr(self):
    if len(self) == 1:
        return self[0]
    return SexpVector.__old_repr__(self)
    
#SexpVector.__old_repr__ = SexpVector.__repr__
#SexpVector.__repr__ = simple_string_vector_repr
