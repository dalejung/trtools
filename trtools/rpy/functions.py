import rpy2.robjects as robjects
import rpy2.robjects.help as rh
r = robjects.r
func_class = robjects.functions.SignatureTranslatedFunction

class RFunction(object):
    def __init__(self, func, name):
        self.func = func
        self.name = name
        self._set_doc()

    def _set_doc(self):
        pages = rh.pages(self.name)
        if len(pages) == 0:
            return

        help = pages[0].to_docstring()
        lines = [line.strip() for line in help.splitlines()]
        doc = "\n".join(lines)
        doc = doc.replace("\n\n", "\n")
        self.__doc__ = doc

    def __call__(self, *args, **kwargs):
        res = self.func(*args, **kwargs)
        return res

    def code(self):
        print self.func.r_repr()

    def __repr__(self):
        return "RFunction: "+self.name

def get_func(name):
    func = r[name]
    if not isinstance(func, func_class):
        raise Exception("R variable is not a function")
    wrapped = RFunction(func, name)
    return wrapped
