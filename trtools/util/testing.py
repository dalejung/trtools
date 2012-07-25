from StringIO import StringIO
import time

from pandas.util.testing import *

class TestStringIO(StringIO):
    def close(self):
        pass

    def free(self):
        StringIO.close(self)

class Timer:
    """
        Usage:

        with Timer() as t:
            ret = func(df)
        print(t.interval)
    """
    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start
