from unittest import TestCase
import os.path
from StringIO import StringIO


import trtools.io.caching_dict as cdict

def curpath():
    pth, _ = os.path.split(os.path.abspath(__file__))
    return pth

class FakeFile(StringIO):
    """
        Pretty Flimsy fake file. 
        assumes all writes are non-append
    """
    _data = ''

    def close(self):
        pass

    def write(self, data):
        FakeFile._data = data
        StringIO.flush(self)
        StringIO.write(self, data)

class TestDict(cdict.CachingDict):
    fakefile = FakeFile()

    def get_fp(self, mode='rb'):
        TestDict.fakefile.seek(0)
        return TestDict.fakefile

    def clear(self):
        TestDict.fakefile.flush()
        super(TestDict, self).clear()


class TestCachingDict(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_save(self):
        cd = TestDict('test')
        cd['whee'] = 'hello'
        cd['boo'] = 'boo'

        cd2 = TestDict('test')
        assert cd2['whee'] == 'hello'
        assert cd2['boo'] == 'boo'

    def test_update(self):
        cd = TestDict('test')
        cd.clear()
        assert len(cd.keys()) == 0
        cd.update(bob='whee', tom='kat')
        assert cd['bob'] == 'whee'
        assert cd['tom'] == 'kat'

        cd2 = TestDict('test')
        assert cd2['bob'] == 'whee'
        assert cd2['tom'] == 'kat'

    def test_clear(self):
        cd = TestDict('test')
        cd.update(bob='whee', tom='kat')
        assert cd['bob'] == 'whee'
        assert cd['tom'] == 'kat'
        cd.clear()
        assert len(cd.keys()) == 0
        assert 'bob' not in cd.keys()

    def test_not_in(self):
        """
            Make sure that not in tests the keys()
            not sure how to do this atm
        """
        cd = TestDict('test')
        cd.clear()
        assert len(cd.keys()) == 0
        assert 'bob' not in cd



if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
