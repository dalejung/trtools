import sys
from pdb import Pdb
from ipdb.__main__ import update_stdout, def_colors, wrap_sys_excepthook

class Tdb(Pdb):
    def __init__(self, *args, **kwargs):
        Pdb.__init__(self, *args, **kwargs)
        self.botframe = None
        self.quitting = False
        self.stopframe = None
        self.codemap = {}
        self.entered = False

    def add_trace(self, func):
        code = func.func_code
        self.codemap[code] = None

    def dispatch_call(self, frame, arg):
        if not self.entered:
            if frame.f_code in self.codemap:
                self.entered = True
                self._set_stopinfo(frame, None)
                return self.trace_dispatch
            else:
                return None

        # XXX 'arg' is no longer used
        if self.botframe is None:
            # First call of dispatch since reset()
            self.botframe = frame.f_back # (CT) Note that this may also be None!
            return self.trace_dispatch
        if not (self.stop_here(frame) or self.break_anywhere(frame)):
            # No need to trace this function
            return # None
        self.user_call(frame, arg)
        if self.quitting: raise BdbQuit
        return self.trace_dispatch

    def set_trace(self, frame=None):
        """
        """
        update_stdout()
        wrap_sys_excepthook()
        if frame is None:
            frame = sys._getframe().f_back
        #pdb = Tdb(def_colors)
        self.reset()
        self.set_step()
        sys.settrace(self.trace_dispatch)

def with_trace(f):
    @wraps(f)
    def tracing(*args, **kwargs):
        set_trace()
        return f(*args, **kwargs)
    return tracing

class Trace(object):
    def __init__(self, *args):
        self.tdb = Tdb(def_colors)

        if len(args) > 0:
            for func in args:
                if callable(func):
                    self.add_function(func)

    def add_function(self, func):
        self.tdb.add_trace(func)

    def __enter__(self):
        self.tdb.set_trace()

    def __exit__(self, type, value, traceback):
        sys.settrace(None)
