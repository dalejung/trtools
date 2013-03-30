from unittest import TestCase
import itertools

import pandas as pd
import numpy as np

import trtools.util.testing as tm
from trtools.core.columns import MultiIndexGetter, ObjectIndexGetter, LevelWrapper

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
        m = MultiIndexGetter(df, attr='columns')
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

    def test_lev(self):
        """
        Added a lev attribute to MultiIndex to access levels by name
        """
        mi = pd.MultiIndex.from_tuples(sets)
        mi.names = ['limit', 'stop', 'target']
        test = (mi.lev.limit == 0) & (mi.lev.stop == 3)
        assert sum(test) == 10 # should just be one row of targets


def dict_cols():
    df = pd.DataFrame(np.random.randn(N, N), index=ind)
    cols = [dict(zip(('limit', 'stop', 'target'), vals)) for vals in sets]
    df.columns = cols
    ogetter = ObjectIndexGetter(df, attr='columns')
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
    ogetter = ObjectIndexGetter(df, attr='columns')
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
        stops = df.col.stop.values
        for i, s in enumerate(sets):
            assert stops[i] == s[1] # stop is second value of tuple

        # test dicts
        df, ogetter = dict_cols()
        targets = df.col.target.values
        for i, s in enumerate(sets):
            assert targets[i] == s[2] # targets is third value of tuple

class TestLevelWrapper(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        mi = pd.MultiIndex.from_tuples(sets)
        df = pd.DataFrame(np.random.randn(N, N), index=ind)
        df.columns = mi
        df.columns.names = ['limit', 'stop', 'target']
        m = MultiIndexGetter(df, attr='columns')
        self.df = df
        self.m = m

    def test_level_wrapper_mi(self):
        """
        Test level wrapper against MultiIndex
        """
        mi = pd.MultiIndex.from_tuples(sets)
        df = pd.DataFrame(np.random.randn(N, N), index=ind)
        df.columns = mi
        df.columns.names = ['limit', 'stop', 'target']
        m = MultiIndexGetter(df, attr='columns')
        lw = df.columns.lev.limit
        # test some ops
        test = lw == 0
        correct = mi.get_level_values('limit') == 0
        tm.assert_almost_equal(test, correct)

        test = lw > 1
        correct = mi.get_level_values('limit') > 1
        tm.assert_almost_equal(test, correct)

        # test getitem
        assert lw[0] == 0
        assert lw[1] == 1

    def test_level_wrapper_oi(self):
        """
        Test level wrapper against Object Index
        """
        class ObjectCol(object):
            def __init__(self, bob, frank):
                self.bob = bob
                self.frank = frank

            def __repr__(self):
                return "bob={bob},frank={frank}".format(**self.__dict__)

        bobs = [3,4,2,1,2,2,1,]
        franks = range(len(bobs))

        objects = [ObjectCol(bob, frank) for bob, frank in zip(bobs, franks)]
        df = pd.DataFrame({'test'+str(i) : np.random.randn(len(objects)) for i in range(len(objects))})
        df.columns = objects
        assert isinstance(df.columns , pd.Index)

        assert isinstance(df.col.bob, LevelWrapper)
        assert isinstance(df.col.frank, LevelWrapper)

        assert np.all(df.col.bob == bobs) # note that bobs is not monotonic
        assert np.all(df.col.frank == franks)

        # test that labels are unique and monotonic
        assert df.col.bob.labels.is_unique
        assert df.col.bob.labels.is_monotonic
        assert np.all(df.col.bob.labels == np.unique(bobs)) # note np.unique also orders

        # comp
        test = df.col.bob == 1
        correct = np.array(bobs) == 1
        assert np.all(test == correct)

        # only match should be bobs[2]
        test = df.col.bob == df.col.frank
        assert test[2]
        assert sum(test) == 1

        # arithmetic
        test = df.col.bob + 1
        correct = np.array(bobs) + 1
        assert np.all(test == correct)

        test = df.col.bob * 13.2
        correct = np.array(bobs) * 13.2
        assert np.all(test == correct)

        # test against other LevelWrapper
        test = df.col.bob / df.col.bob 
        assert np.all(test == 1)

        test = df.col.bob / df.col.frank 
        correct = np.array(bobs) / np.array(franks)
        assert np.all(test == correct)

    def test_level_wrapper_isclose(self):
        """
        Test that __eq__ uses np.isclose

        # 03-30-13. This fails since __eq__  currently uses __eq__
        """
        mi = pd.MultiIndex.from_arrays([np.linspace(.001, .024, 24)]*2, names=['first', 'second'])
        assert np.any(mi.lev.first == .01)

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
