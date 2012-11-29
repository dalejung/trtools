from line_profiler import LineProfiler

class Profiler(object):

    def __init__(self, *args):
        self.profile = LineProfiler()

        if len(args) > 0:
            for func in args:
                if callable(func):
                    self.add_function(func)

    def add_function(self, func):
        self.profile.add_function(func)

    def __enter__(self):
        self.profile.enable_by_count()

    def __exit__(self, type, value, traceback):
        self.profile.disable_by_count()
        self.profile.print_stats()
