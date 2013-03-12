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
N = len(mi)
ind = pd.date_range(start="2000-01-01", freq="D", periods=N)

df = pd.DataFrame(np.random.randn(N, N), columns=mi, index=ind)
df.columns.names = ['limit', 'stop', 'target']
m = MultiIndexGetter(df)

class TestColumns(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_multiindexgetter(self):
        test = df.ix[:, (m.limit == 0) & (m.stop == 3)]
        assert len(test.columns) == 10 # should just be one row of targets

    def test_property_cx(self):
        test = df.ix[:, (df.col.limit == 0) & (df.col.stop == 3)]
        assert len(test.columns) == 10 # should just be one row of targets

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
