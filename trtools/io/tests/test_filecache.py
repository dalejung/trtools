from unittest import TestCase
from io import StringIO

from trtools.util.tempdir import TemporaryDirectory
import trtools.io.filecache as fc

class TestFileCache(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

class MetaKey(object):
    def __init__(self, key):
        self.key = key

    def __hash__(self):
        return hash(self.key)

    def __filename__(self):
        return str(self.key) + '.save'

    def __repr__(self):
        return repr(self.key)

class Value(object):
    def __init__(self, string):
        self.string = string


class TestMetaFileCache(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass
    def test_meta(self):
        key1 = MetaKey('dale')
        key2 = MetaKey('bob')

        with TemporaryDirectory() as td:
            mfc = fc.MetaFileCache(td)
            mfc[key1] = Value('daledata')
            mfc[key2] = Value('bobdata')
            mfc[key1] = Value('daledata2')

            # grabbing with key still works
            assert mfc[key1].string == 'daledata2'

            # this one should load keys from index file
            mfc2 = fc.MetaFileCache(td)
            for a,b in zip( list(mfc2.keys()), list(mfc.keys())):
                assert a.key == b.key

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
