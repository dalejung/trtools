from unittest import TestCase
import itertools

import pandas as pd
import numpy as np

import trtools.util.testing as tm
from trtools.core.columns import MultiIndexGetter

limit = range(10)
stop = range(3,7)
target = range(10, 20)

sets = itertools.product(limit, stop, target)
sets = list(sets)

mi = pd.MultiIndex.from_tuples(sets)
mi.names = ['limit', 'stop', 'target']
N = len(mi)
ind = pd.date_range(start="2000-01-01", freq="D", periods=N)

df = pd.DataFrame(np.random.randn(N, N), columns=mi, index=ind)

class TestColumns(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_multiindexgetter(self):
        m = MultiIndexGetter(mi)
        df.ix[:, m.limit == 0]

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
