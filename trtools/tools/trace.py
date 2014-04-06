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
        self.codemap[code] = 0

    def trace_dispatch(self, frame, event, arg):
        if self.quitting:
            return # None
        if event == 'line':
            return self.dispatch_line(frame)
        if event == 'call':
            return self.dispatch_call(frame, arg)
        if event == 'return':
            return self.dispatch_return(frame, arg)
        if event == 'exception':
            return self.dispatch_exception(frame, arg)
        if event == 'c_call':
            return self.trace_dispatch
        if event == 'c_exception':
            return self.trace_dispatch
        if event == 'c_return':
            return self.trace_dispatch
        print 'bdb.Bdb.dispatch: unknown debugging event:', repr(event)
        return self.trace_dispatch


    def dispatch_call(self, frame, arg):
        if not self.entered:
            f_code = frame.f_code
            if f_code in self.codemap:
                self.entered = True
                self.codemap[f_code] += 1
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

        funcs = filter(callable, args)
        for func in funcs:
            self.add_function(func)

    def add_function(self, func):
        self.tdb.add_trace(func)

    def __enter__(self):
        self.tdb.set_trace()
        return self

    def __exit__(self, type, value, traceback):
        sys.settrace(None)
