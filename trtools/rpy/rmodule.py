"""
    Make R packages act more like modules. 
    
    This includes making functions easier to use and wrapping R packages.
"""
import rpy2.robjects as robjects
import rpy2.robjects.help as rh
from rpy2.robjects.packages import importr
import rpy2.robjects.packages as rpacks
r = robjects.r
func_class = robjects.functions.SignatureTranslatedFunction

import pandas as pd

class RFunction(object):
    """
        More convenient R function access
    """
    def __init__(self, func, name):
        self.func = func
        self.name = name
        self.title = ""
        self.description = ""
        self._set_doc()

    def _set_doc(self):
        help = self._help()
        if help is None:
            return
        lines = [line.strip() for line in help.to_docstring().splitlines()]
        doc = "\n".join(lines)
        doc = doc.replace("\n\n", "\n")
        self.__doc__ = doc
        self.title = help.title().strip()
        self.description = help.description().strip()

    def _help(self):
        pages = rh.pages(self.name)
        if len(pages) == 0:
            return None

        help = pages[0]
        return help

    def __call__(self, *args, **kwargs):
        res = self.func(*args, **kwargs)
        return res

    def _code(self):
        return self.func.r_repr()

    def code(self):
        print self._code()

    def __repr__(self):
        env_name = ""
        try:
            env = rpacks.wherefrom(self.name)
            env_name = env.do_slot('name')[0]
        except:
            pass
        vars = ["RFunction: {0}".format(self.name)]
        if self.title:
            title = "Title:\n\n{0}".format(self.title)
            vars.append(title)
        if self.description:
            desc = "Description:\n\n{0}".format(self.description)
            vars.append(desc)
        if env_name:
            envs = "<{0}>".format(env_name)
            vars.append(envs)
        return "\n\n".join(vars)

def get_func(r_name):
    func = r[r_name]
    return wrap_func(func, r_name)

def wrap_func(func, r_name):
    if not isinstance(func, func_class):
        raise Exception("R variable is not a function")
    wrapped = RFunction(func, r_name)
    return wrapped

class DotWrapper(object):
    """
        This handles cases where dot (.) is used in function names for namespacing.
        This class will properly handle namespacing such as SharpeRatio.annualized while also 
        supporting SharpRatio itself being a function
    """
    def __init__(self, pkg, name):
        self._cache = {}
        self._name = name
        self._pkg = pkg
        self._subgroup = self._pkg.subgroup(name)
        self._funcs = self._subgroup.func_name.unique()

        # init __doc__ if base func exists
        r_name = self._name
        func = self._func(r_name)
        self.base_func = func
        if func:
            self.__doc__ = func.__doc__

    def _init_funcs(self):
        for i, row in self._subgroup.iterrows():
            r_name = row['r']
            bits = r_name.split('.')
            if len(bits) == 1:
                continue
            func = self._func(r_name)
            try:
                setattr(self, bits[1], func)
            except:
                print "{0} failed to bind".format(r_name)

    def __call__(self, *args, **kwargs):
        func = self.base_func
        if func is None:
            raise Exception("RFunction does not exist")
        return func(*args, **kwargs)

    def __getattr__(self, key):
        r_name = self._name + '.' + key
        func = self._func(r_name)
        if func:
            return func

        # check if main func exists
        # this is so SharpRatio.code() works
        r_name = self._name
        func = self._func(r_name)
        if func and hasattr(func, key):
            return getattr(func, key)

        raise AttributeError("No {0} function in {1} namespace".format(key, self._name))

    def _func(self, r_name):
        if r_name in self._cache:
            return self._cache[r_name]

        if r_name in self._subgroup.r.values:
            func = self._pkg.r_name(r_name)
            func = wrap_func(func, r_name)
            self._cache[r_name] = func
            return self._cache[r_name]

        return None

    def __repr__(self):
        if self.base_func:
            return repr(self.base_func)
        return self._pkg.name + '.' + self._name

class RPackage(object):
    """
        Wraps around an rpy2 package. Note, that importr seems to access names that 
        don't appear from a require() call. I think it ignores the explicit namespace
        exporting
    """
    def __init__(self, name, translations=None):
        self.name = name
        if translations is None:
            translations = {}
        self.pkg = importr(name, robject_translations=translations)
        self._create_table(self.pkg._rpy2r.items())
        self._cache = {}

    def __getattr__(self, key):
        cache = self._cache
        if key in cache:
            return cache[key]
        subgroup = self.subgroup(key)
        if len(subgroup) > 0:
            cache[key] = DotWrapper(self, key)
            return cache[key]
        raise AttributeError("No name in package")

    def _create_table(self, rpy2r):
        self.table = pd.DataFrame(rpy2r, columns=['rpy', 'r'])
        # split out sub namespaces
        words = self.table.r.str.split('.')
        self.table['subgroup'] = words.apply(lambda x: x[0])
        self.table['func_name'] = words.apply(lambda x: len(x) > 1 and x[1] or None)

        is_func = self.table.rpy.apply(self._is_func)
        self.table['is_func'] = is_func

        # only subgroupping funcs
        subgroups = self.table[self.table.is_func].subgroup
        self._subgroups = subgroups[subgroups != '']

    def _is_func(self, name):
        func = getattr(self.pkg, name)
        return isinstance(func, func_class)

    def subgroup(self, name):
        return self.table[self.table.subgroup == name]

    def r_name(self, r_name):
        """
            Grab pkg variable based on r_name which can include periods
        """
        row = self.table[self.table.r == r_name]
        if len(row) == 0:
            return None
        rpy_name = row.irow(0)['rpy']
        return getattr(self.pkg, rpy_name)

    def __iter__(self):
        return iter(self._subgroups)


# IPYTYHON
def install_ipython_completers():  # pragma: no cover
    """Register the DataFrame type with IPython's tab completion machinery, so
    that it knows about accessing column names as attributes."""
    from IPython.utils.generics import complete_object
    from pandas import compat

    @complete_object.when_type(RPackage)
    def complete_rpackage(obj, prev_completions):
        return prev_completions + [c for c in obj._subgroups \
                    if isinstance(c, basestring) and compat.isidentifier(c)]                                          
    @complete_object.when_type(DotWrapper)
    def complete_dot_wrapper(obj, prev_completions):
        return prev_completions + [c for c in obj._funcs \
                    if isinstance(c, basestring) and compat.isidentifier(c)]                                          

# Importing IPython brings in about 200 modules, so we want to avoid it unless
# we're in IPython (when those modules are loaded anyway).
import sys
if "IPython" in sys.modules:  # pragma: no cover
    try: 
        install_ipython_completers()
    except Exception:
        pass 
