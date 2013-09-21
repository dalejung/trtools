from collections import OrderedDict
missing = object()

class attrdict(OrderedDict):
    """A dict whose items can also be accessed as member variables.

    >>> d = attrdict(a=1, b=2)
    >>> d['c'] = 3
    >>> print d.a, d.b, d.c
    1 2 3
    >>> d.b = 10
    >>> print d['b']
    10

    # but be careful, it's easy to hide methods
    >>> print d.get('c')
    3
    >>> d['get'] = 4
    >>> print d.get('a')
    Traceback (most recent call last):
    TypeError: 'int' object is not callable
    """
    def __init__(self, *args, **kwargs):
        OrderedDict.__init__(self, *args, **kwargs)

    def __getattr__(self, name):
        try:
             return self[name]
        except:
            pass
        return OrderedDict.__getattribute__(self, name)

    def __getitem__(self, name):
        """
            A regular key in dict will match on hash. 

            This version matches on __eq__ if the hash doesn't match.

            # NOTE: This can possibly lead to both perf hits and situations
            # where two keys match the same other. 
        """
        # regular ole dict check
        if name in self:
            return dict.__getitem__(self, name)

        # list.__contains__ uses eq() to check membership
        keys = self.keys()
        if name in keys:
            ind = keys.index(name)
            return self[keys[ind]]
        raise KeyError()

    def __repr__(self):
        out = 'Keys:\n'
        out += '\n'.join([str(k) for k in self.keys()])
        return out

    def foreach(self, key=None, func=missing):
        """
        A convenient way to get a subset of results. 

        I often use attrdict to store DataFrames with a common
        column indexes. This allows me to quickly get a subset
        """
        if func is None and key is None:
            raise ValueError('invalid number of arguments')

        if func is missing:
            func = lambda dct, key: dct[key]

        res = attrdict()
        for k, v in self.iteritems():
            try:
                res[k] = func(v, key)
            except:
                pass
        return res

# IPYTYHON
def install_ipython_completers():  # pragma: no cover
    """Register the DataFrame type with IPython's tab completion machinery, so
    that it knows about accessing column names as attributes."""
    from IPython.utils.generics import complete_object
    from pandas import compat

    @complete_object.when_type(attrdict)
    def complete_attrdict(obj, prev_completions):
        return prev_completions + [c for c in obj.keys() \
                    if isinstance(c, basestring) and compat.isidentifier(c)]                                          

# Importing IPython brings in about 200 modules, so we want to avoid it unless
# we're in IPython (when those modules are loaded anyway).
import sys
if "IPython" in sys.modules:  # pragma: no cover
    try: 
        install_ipython_completers()
    except Exception:
        pass 
