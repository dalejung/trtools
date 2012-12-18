from unittest import TestCase

import numpy as np
import pandas as pd
import pandas.util.testing as tm

import trtools.monkey as monkey
reload(monkey)

series = pd.Series(['dale', 'bob', 'test', 'pandas', 'dales', 'whale'])

class TestMonkey(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_attr_proxy(self):
        def callback_key(obj, key):
            return key

        def callback_delegate(obj, key):
            import operator
            f = operator.attrgetter(key)
            return f(obj)

        ap = monkey.AttrProxy('str', series, callback=callback_key)
        test_key = ap.startswith
        assert test_key == 'str.startswith'

        ap2 = monkey.AttrProxy('str', series, callback=callback_delegate)
        test_func = ap2.startswith
        assert callable(test_func)
        assert np.all(test_func('ale') == series.str.startswith('ale'))

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
