import warnings
import functools 

def patch(classes, name=None):
    if not isinstance(classes, list):
        classes = [classes]

    def decorator(func):
        for cls in classes:
            func_name = name and name or func.__name__
            old_func_name = '_old_'+func_name
            if hasattr(cls, old_func_name):
                warnings.warn("{0} was already monkey patched. Detected _old_ func".format(func_name))
                continue

            if hasattr(cls, func_name):
                old_func = getattr(cls, func_name)
                setattr(cls, old_func_name, old_func)
            setattr(cls, func_name, func)
        return func
    return decorator

def patch_prop(classes, name=None):
    if not isinstance(classes, list):
        classes = [classes]

    def decorator(func):
        for cls in classes:
            prop_name = name and name or func.__name__
            func_name = '_func_'+prop_name        
            setattr(cls, func_name, func)
            prop = property(func)
            setattr(cls, prop_name, prop)

        return func
    return decorator

def patcher(classes, func, name=None):
    if not isinstance(classes, list):
        classes = [classes]

    for cls in classes:
        func_name = name and name or func.__name__
        old_func_name = '_old_'+func_name
        if hasattr(cls, old_func_name):
            warnings.warn("{0} was already monkey patched. Detected _old_ func".format(func_name))
            continue

        if hasattr(cls, func_name):
            old_func = getattr(cls, func_name)
            setattr(cls, old_func_name, old_func)
        setattr(cls, func_name, func)
    return func

class AttrNameSpace(object):
    """
    """
    def __init__(self, obj, endpoint):
        self.obj = obj
        self.endpoint = endpoint
        self.wrap = True
        if hasattr(self.endpoint, '__getattr__'):
            # don't wrap, assume endpoint is wrapping
            self.wrap = False
            self.endpoint.obj = obj

    def __getattr__(self, name):
        func = getattr(self.endpoint, name)
        if self.wrap:
            func = functools.partial(func, self.obj)
        return func

    def method_attrs(self):
        import inspect
        attrs = inspect.getmembers(self.endpoint, predicate=inspect.ismethod)
        attrs = [attr for attr, type in attrs]
        return attrs

    def attrs(self):
        attrs = []
        if self.wrap:
            attrs = self.method_attrs()
        if not self.wrap and hasattr(self.endpoint, 'attrs'):
            attrs = self.endpoint.attrs()
        return attrs

    def __repr__(self):
        out = "AttrNameSpace:\n"

        attrs = self.attrs()
        if attrs:
            out += "\n".join(attrs)
        return out

def attr_namespace(target, name):
    """
        Use to create Attribute Namespace. 

        @attr_namespace(pd.DataFrame, 'ret')
        class Returns(object):
            def log_returns(df):
                return np.log(df.close / df.close.shift(1))

        You could access via df.ret.log_returns
    """

    def func(cls):
        def attr_get(self):
            attr_name = '_attr_ns_'+name
            if not hasattr(self, attr_name):
                setattr(self, attr_name, AttrNameSpace(self, cls()))

            return getattr(self, attr_name)

        patch_prop(target, name)(attr_get)
        return cls

    return func

# IPYTYHON
# Autocomplete the target endpoint
def install_ipython_completers():  # pragma: no cover
    from pandas.util import py3compat
    from IPython.utils.generics import complete_object

    @complete_object.when_type(AttrNameSpace)
    def complete_column_panel(self, prev_completions):
        return [c for c in self.attrs() \
                    if isinstance(c, basestring) and py3compat.isidentifier(c)]                                          
# Importing IPython brings in about 200 modules, so we want to avoid it unless
# we're in IPython (when those modules are loaded anyway).
import sys
if "IPython" in sys.modules:  # pragma: no cover
    try: 
        install_ipython_completers()
    except Exception:
        pass 
