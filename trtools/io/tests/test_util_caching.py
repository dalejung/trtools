import os.path

from unittest import TestCase

from trtools.io.cacher import cacher

class TestClass(object):
    def __init__(self):
        self.count = 0

    @cacher('test/test_meth', method=True)
    def test_meth(self):
        self.count += 1
        return self.count

    def test_meth2(self):
        self.count += 1
        return self.count

class TestCaching(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_cache_clear(self):
        """
            test cacher.clear
        """
        tc = TestClass()
        tc.test_meth.cacher.clear()
        assert tc.test_meth.cacher.cache == {}
        assert not os.path.isfile(tc.test_meth.cacher.filepath)
        tc.test_meth()
        assert tc.test_meth.cacher.cache != {}

    def test_cache_method_type(self):
        """
            test that caching works with method types
        """
        tc = TestClass()
        tc.test_meth.cacher.clear()
        assert tc.count == 0
        ret = tc.test_meth()
        assert ret == 1
        assert tc.count == 1
        ret = tc.test_meth()
        assert ret == 1
        assert tc.count == 1

        tc = TestClass()
        assert tc.count == 0
        ret = tc.test_meth()
        assert ret == 1
        # should have grabbed from file and not ran test_meth
        assert tc.count == 0

        # test non cached
        tc = TestClass()
        assert tc.count == 0
        tc.test_meth2()
        assert tc.count == 1
        tc.test_meth2()
        assert tc.count == 2

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
