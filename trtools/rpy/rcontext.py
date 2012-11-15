import collections

from rpy2.rlike.container import TaggedList

import rpy2.robjects as robjects
r = robjects.r

def _r(val):
    """
    Convert val to valid R code
    """
    if isinstance(val, basestring):
        # no quoting quote
        if val.startswith("quote("): 
            return val
        return '"{0}"'.format(val)

    if val is True:
        return "TRUE"
    if val is False:
        return "FALSE"

    if isinstance(val, collections.Iterable):
        return "c({0})".format(','.join([_r(v) for v in val]))

    # this could probably be more robust
    if hasattr(val, 'r_repr'):
        return val.r_repr()

    return val

class DefaultR(object):
    """
        Default namespacing for RContext
    """
    TRUE = True
    FALSE = False

    def __iter__(self):
        return iter(['c', 'list', 'TRUE', 'FALSE', 'quote'])

    @staticmethod
    def c(*args):
        return TaggedList(args)

    @staticmethod
    def list(**kwargs):
        parts = ["{0}={1}".format(k,_r(v)) for k,v in kwargs.items()]
        list_string = ','.join(parts)
        list_cmd = "list({0})".format(list_string)
        tl = r(list_cmd)
        return tl

    @staticmethod
    def quote(cmd):
        """
            For now, quote returns just a string which is handled in
            list() via _r().

            That means that quote only works within lists. 
            Currently a limitation of rpy not handling calls 
            that aren't wrapped in lists
            # https://bitbucket.org/lgautier/rpy2/issue/110/handling-mode-call-variables-preventing
        """
        return "quote({0})".format(cmd)

def mesh_vars(vars, obj, names=None):
    if names is None:
        names = iter(obj)

    overridden = {}
    for name in names:
        if name in vars:
            overridden[name] = vars[name]
        else:
            overridden[name] = None
        vars[name] = getattr(obj, name)

    return overridden

class RContext(object):
    def __init__(self, packages, scope):
        self.packages = packages 
        self.change_list = {}
        self.scope = scope

    def enable_package(self, pkg):
        vars = self.scope
        over = mesh_vars(vars, pkg)
        self.change_list.update(over)

    def __enter__(self):
        self.change_list = {} # reset
        self.enable_package(DefaultR())

        # Need to find a way to coalese the subgroups
        # quantstrat last so add.XXX isn't clobbered
        for pkg in self.packages:
            self.enable_package(pkg)

        vars = self.scope
        vars['_overridden'] = self.change_list

    def __exit__(self, type, value, traceback):
        # reset globals
        vars = self.scope
        for key, val in self.change_list.iteritems():
            if val is None:
                del vars[key]
                continue
            vars[key] = val
