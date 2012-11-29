from line_profiler import LineProfiler

class Profiler(object):

    def __init__(self, funcs=None):
        self.profile = LineProfiler()

        if funcs:
            for func in funcs:
                self.add_function(func)

    def add_function(self, func):
        self.profile.add_function(func)

    def __enter__(self):
        self.profile.enable_by_count()

    def __exit__(self, type, value, traceback):
        self.profile.disable_by_count()
        self.profile.print_stats()
