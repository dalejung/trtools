import imp
import sys
import imputil

# http://www.python.org/dev/peps/pep-0302/

MODULE_CACHE = {}

class DataImportFinder(object):
    def __init__(self, *args):
        pass
 
    def find_module(self, fullname, path=None):
        mname = fullname.rpartition('.')[-1]
        try:
            res = imp.find_module(mname, path)
        except ImportError:
            return None

        loader = DataImportLoader(mname, path)
        return loader

class DataImportLoader(imputil.Importer):
    def __init__(self, mname, path):
        self.mname = mname
        self.path = path
 
    def load_module(self, fullname):
        # first time load normally
        if fullname not in sys.modules:
            module = self.load_first(fullname)
            return module

        module = sys.modules[fullname]
        return module

    def load_first(self, fullname):
        mname = self.mname
        fp, pathname, description = imp.find_module(mname, self.path)

        module = imp.load_module(mname, fp, pathname, description)

        sys.modules[fullname] = module
        return module

def _get_source(mname, path=None):
    fp, pathname, desc = imp.find_module(mname, [path])
    if fp:
        source = fp.read()
        return source

def _get_dataimport_vars(source):
    lines = source.splitlines()
    di_lines = []
    for line in lines:
        if line.startswith('DATAIMPORT_'):
            di_lines.append(line)
        else:
            break

    di_source = '\n'.join(di_lines)
    di_vars = {}
    exec di_source in di_vars
    return di_vars
 
def install_data_import():
    sys.meta_path = [DataImportFinder()]

