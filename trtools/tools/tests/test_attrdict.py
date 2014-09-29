from unittest import TestCase
from trtools.tools import attrdict

class TestKey(object):
    """
        Dummy key that checks against string member if other is string
    """
    def __init__(self, string, number):
        self.string = string 
        self.number = number

    def __eq__(self, other):
        if isinstance(other, str):
            return self.string == other
        return self.number == other

class TestAPI(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_string_keys(self):
        d = attrdict()
        d['dale'] = 123
        assert d.dale == 123
        assert d['dale'] == 123

    def test_object_keys(self):
        """
            Test that object keys work. The point of object keys is that they can
            have multiple paths of eq() check. A regular dictionary will check 
            using is or hash(self) == hash(other). We turn this check into eq(self, other). 

            This means we can use keys that can have multiple types of equivalencies.
        """
        d = attrdict()
        k = TestKey('dale', 111)
        d[k] = 'test'
        k = TestKey('dale2', 112)
        o = object()
        d[k] = o

        assert d.dale == 'test'
        assert d[111] == 'test'
        assert d['dale'] == 'test'

        assert d[112] is d['dale2']

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
