from unittest import TestCase
import itertools

import pandas as pd
import numpy as np

import trtools.util.testing as tm
from trtools.core.columns import MultiIndexGetter, ObjectIndexGetter

limit = range(10)
stop = range(3,7)
target = range(10, 20)

sets = itertools.product(limit, stop, target)
sets = list(sets)

N = len(sets)
ind = pd.date_range(start="2000-01-01", freq="D", periods=N)


class TestMultiIndexGetter(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        mi = pd.MultiIndex.from_tuples(sets)
        df = pd.DataFrame(np.random.randn(N, N), index=ind)
        df.columns = mi
        df.columns.names = ['limit', 'stop', 'target']
        m = MultiIndexGetter(df)
        self.df = df
        self.m = m

    def test_multiindexgetter(self):
        m = self.m
        df = self.df
        test = df.ix[:, (m.limit == 0) & (m.stop == 3)]
        assert len(test.columns) == 10 # should just be one row of targets

    def test_property_col(self):
        df = self.df
        test = df.ix[:, (df.col.limit == 0) & (df.col.stop == 3)]
        assert len(test.columns) == 10 # should just be one row of targets

def dict_cols():
    df = pd.DataFrame(np.random.randn(N, N), index=ind)
    cols = [dict(zip(('limit', 'stop', 'target'), vals)) for vals in sets]
    df.columns = cols
    ogetter = ObjectIndexGetter(df)
    return df, ogetter

def object_cols():
    class Object(object):
        def __init__(self, dct):
            for k, v in dct.items():
                setattr(self, k, v)

    dicts = [dict(zip(('limit', 'stop', 'target'), vals)) for vals in sets]
    cols = [Object(d)  for d in dicts]

    df = pd.DataFrame(np.random.randn(N, N), index=ind)
    df.columns = cols
    ogetter = ObjectIndexGetter(df)
    return df, ogetter

class TestObjectIndexGetter(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_names_keys(self):
        # this uses __dict__ names
        df, ogetter = dict_cols()
        col = df.columns[0]
        assert hasattr(col, 'keys') # dict has uses keys()
        assert set(ogetter.names) == set(['limit', 'stop', 'target'])

    def test_names__dict__(self):
        # this uses __dict__ names
        df, ogetter = object_cols()
        col = df.columns[0]
        assert not hasattr(col, 'keys') # Object has no keys method
        assert set(ogetter.names) == set(['limit', 'stop', 'target'])

    def test_col(self):
        df, ogetter = object_cols()
        stops = df.col.stop
        for i, s in enumerate(sets):
            assert stops[i] == s[1] # stop is second value of tuple

        # test dicts
        df, ogetter = dict_cols()
        targets = df.col.target
        for i, s in enumerate(sets):
            assert targets[i] == s[2] # targets is third value of tuple

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
