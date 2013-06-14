from collections import OrderedDict
import types
import ast
import imp
import sys
import imputil

# http://www.python.org/dev/peps/pep-0302/

MODULE_VAR_CACHE = {}

def _get_di_vars(code):
    data = OrderedDict()
    for node in code.body:
        if isinstance(node, ast.Assign):
            try:
                names = [n.id for n in node.targets]
                value = ast.literal_eval(node.value)
            except:
                continue

            names = [name for name in names if name.startswith('DATAIMPORT')]
            for name in names:
                data[name] = value
    return data

def _cache_key(fullname, config):
    custom_key = config.get('DATAIMPORT_CACHE_KEY', None)
    return custom_key or fullname

class DataImportLoader(imputil.Importer):
    def __init__(self, fullname, path):
        self.fullname = fullname
        self.path = path
        mname = fullname.rpartition('.')[-1]
        self.mname = mname

    def load_module(self, fullname):
        """
        Note:
        -----
        We do not cache module in sys.modules
        """
        mname = self.mname
        fp, pathname, desc = imp.find_module(mname, self.path)
        suffix, mode, type = desc

        source = fp.read()
        code = ast.parse(source, pathname)
        config = _get_di_vars(code)
        # LOAD CACHE
        cache = self.load_cache(config)
        # process the ast and remove the cache vars
        code = self.process_ast(code, config, cache)

        code = compile(code, pathname, 'exec')
        mod = self.new_module()
        ns = {}
        # populate namespace with cache vars
        ns.update(cache)
        exec code in ns
        mod.__dict__.update(ns)

        # SAVE CACHE
        self.save_cache(ns, config)
        return mod

    # in process cache
    def load_cache(self, config):
        cache_key = _cache_key(self.fullname, config)
        cache = MODULE_VAR_CACHE.get(cache_key, {})
        return cache

    def save_cache(self, vars, config):
        SKIP_TYPES = (types.ModuleType, types.FunctionType, types.LambdaType, 
                     types.ClassType, types.FileType)
        vars = {k:v for k, v in vars.iteritems() 
                if not isinstance(v, SKIP_TYPES)}
        vars.pop('__builtins__', None)

        cache_key = _cache_key(self.fullname, config)
        MODULE_VAR_CACHE[cache_key] = vars

    def process_ast(self, code, config, cache):
        new_body = skip_nodes_in_cache(code.body, cache)
        code.body = new_body
        return code

    def new_module(self):
        mname = self.mname
        mod = imp.new_module(mname)
        mod.__path__ = self.path
        return mod

class DataImportFinder(object):
    def __init__(self, loader_class=None):
        if loader_class is None:
            loader_class = DataImportLoader
        self.loader_class = loader_class
 
    def find_module(self, fullname, path=None):
        """
        Only match DataImport modules
        """
        mname = fullname.rpartition('.')[-1]
        try:
            fp, pathname, desc = imp.find_module(mname, path)
            suffix, mode, type = desc
        except ImportError:
            return None

        # skip packages or non .py files
        if fp is None or type != imp.PY_SOURCE:
            return None

        source = fp.read()
        code = ast.parse(source, pathname)
        config = _get_di_vars(code)

        # no dataimport variables
        if len(config) == 0:
            return None

        loader = self.loader_class(fullname, path)
        return loader

def skip_nodes_in_cache(nodes, cache):
    # remove the assign statements that were gotten 
    # from cache
    new_body = []
    for node in nodes:
        res = _skip_node(node, cache)
        if not res:
            new_body.append(node)
    return new_body

def _skip_node(node, cache):
    if not isinstance(node, ast.Assign):
        return False

    # only handle single assignments
    if len(node.targets) > 1:
        return False

    try:
        name = node.targets[0].id
    except:
        return False

    if name in cache:
        return True


def install_data_import(loader_class=None):
    sys.meta_path = [DataImportFinder(loader_class)]

"""
Check if cache has data
if cache:
    load from cache
    create_new_module
    update module dict
else:
    load module
    save cache 
"""
