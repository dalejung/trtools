from StringIO import StringIO

from pandas.util.testing import *

class TestStringIO(StringIO):
    def close(self):
        pass

    def free(self):
        StringIO.close(self)
