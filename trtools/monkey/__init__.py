import warnings
import functools 

def patch(classes, name=None, override=False):
    if not isinstance(classes, list):
        classes = [classes]

    def decorator(func):
        for cls in classes:
            func_name = name and name or func.__name__
            old_func_name = '_old_'+func_name


            old_func = getattr(cls, old_func_name, None)
            if old_func is not None and not override:
                warnings.warn("{0} was already monkey patched. Detected _old_ func".format(func_name))
                continue

            # do not override old_func_name, which should always point to original
            if old_func is None and hasattr(cls, func_name):
                old_func = getattr(cls, func_name)
                setattr(cls, old_func_name, old_func)

            setattr(cls, func_name, func)
        return func
    return decorator

def patch_prop(classes, name=None):
    """
    Wraps around patch and sends it a property(func)
    """
    if not isinstance(classes, list):
        classes = [classes]

    def decorator(func):
        for cls in classes:
            prop_name = name and name or func.__name__
            prop = property(func)
            patch(cls, name=prop_name)(prop)
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
    AttrNameSpace does not define the namespace. It is merely a middleman that translates
    attribute access for obj.attr and relays it to the proper endpoint.

    Note on wrapping. AttrNameSpace will try to replicate a normal method call by passing in
    self.obj into function calls. That means that a regular NameSpace.method will receive
    two parameters, (AttrNameSpace.endpoint, AttrNameSpace.obj). 

    If there is no reason for access to the endpoint, then make its methods static. 

    That way, the method will only receive the .obj and will acts as if it's a normal method of obj. 

    The first purpose of this class is for organization. It is taking flat namespace with 100 methods, 
    and splitting some off into their own namespace without altering their functionality. 

    Storing state in the endpoint and accessing it is permissable, but not the primary function. 
    """
    def __init__(self, obj, endpoint, name):
        """
        Parameters
        ----------
        obj : object
        endpoint : object
        name : string
            The attr name of obj that endpoint takes over.
        """
        self.obj = obj
        self.endpoint = endpoint
        self.name = name
        self.wrap = True
        if hasattr(self.endpoint, '__getattr__'):
            # don't wrap, assume endpoint is wrapping
            self.wrap = False
            self.endpoint.obj = obj

        # on creation, store easy ref to overriden function if it exists
        self._old_func = self._get_old_func()

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

        # add info for old_func
        if self._old_func:
            out += "\n\nOverridden method: \n"
            out += 'Docstring:\t'+self._old_func.__doc__
            # TODO add more info
        return out

    def _get_old_func(self):
        func_name = '_old_' + self.name
        func = getattr(self.obj, func_name, None)
        return func

    def __call__(self, *args, **kwargs):
        func = self._old_func
        if func and callable(func):
            return func(*args, **kwargs)
        raise TypeError("{attr} on {obj} was not callable".format(attr=self.name, obj=str(self.obj)))


def attr_namespace(target, name):
    """
        Use to create Attribute Namespace. 

        @attr_namespace(pd.DataFrame, 'ret')
        class Returns(object):
            def log_returns(df):
                return np.log(df.close / df.close.shift(1))

        You could access via df.ret.log_returns
    """

    def class_wrap(cls):
        def attr_get(self):
            # create namespace
            attr_ns = AttrNameSpace(self, cls(), name)
            return attr_ns
        patch_prop(target, name)(attr_get)
        return cls

    return class_wrap

class AttrProxy(object):
    """
       Wraps an object and exposes its attribute which are 
       run through a callback. 

       This is a utility class for wrapping other objects. Usually
       one would override the __getattr__ and delegate to the wrapped
       class. However, that breaks down when the attribute is an object,
       and you want to wrap that attribute's methods. 

        The use case is for ColumnPanel which allows things like
        cp.tail(10) which calls tail(10) for each frame. Currently, 
        this does not work for nested objects. cp.ret.log_returns() 
        would not work
    """
    def __init__(self, name, obj, callback):
        self.name = name
        self.obj = obj
        self.attr = getattr(obj, name)
        self.callback = callback

    def __getattr__(self, key):
        if hasattr(self.attr, key):
            fullattr = '.'.join([self.name, key])
            return self.callback(self.obj, fullattr)
        raise AttributeError()

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
