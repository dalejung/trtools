from unittest import TestCase

import pandas as pd
import numpy as np

import trtools.core.wrangling as wrangling
reload(wrangling)
import trtools.util.testing as tm
from trtools.tools.profiler import Profiler
pairwise = wrangling.pairwise

ind = pd.date_range(start="2000-01-01", freq="D", periods=300)
columns = ['col'+str(i) for i in range(50)]
df = pd.DataFrame(np.random.randn(len(ind), len(columns)), index=ind, columns=columns)

class TestWrangling(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_pairwise(self):
        df = pd.DataFrame(index=range(10))
        for x in range(3):
            df[x] = range(x, x+10)

        nandf = df.copy().astype(float)
        nandf.ix[9:,1] = np.nan

        # test with order=True
        # test with permutations
        pairs = pairwise(df, lambda x, y: x.sum() - y.sum())
        expected = pd.DataFrame([[0, -10, -20], 
                                 [10, 0, -10],
                                 [20, 10, 0]], index=range(3), dtype=float)
        tm.assert_frame_equal(pairs, expected)

        # test with combinations
        pairs = pairwise(df, lambda x, y: x.sum() - y.sum(), order=False)
        expected = pd.DataFrame([[0, -10, -20], 
                                 [-10, 0, -10],
                                 [-20, -10, 0]], index=range(3), dtype=float)
        tm.assert_frame_equal(pairs, expected)

        # test with combinations and values
        # use nandf to test. np.ndarray.sum() returns NaN if it contains nan
        pairs = pairwise(nandf, lambda x, y: x.sum() - y.sum(), order=True, 
                         force_values=True)
        expected = pd.DataFrame([[0, np.nan, -20], 
                                 [np.nan, np.nan, np.nan],
                                 [20, np.nan, 0]], index=range(3), dtype=float)
        tm.assert_frame_equal(pairs, expected)

        # test with np.nansum.
        pairs = pairwise(nandf, lambda x, y: np.nansum(x) - np.nansum(y), 
                         order=True, force_values=True)
        expected = pd.DataFrame([[0, 0, -20], 
                                 [0, 0, -20],
                                 [20, 20, 0]], index=range(3), dtype=float)
        tm.assert_frame_equal(pairs, expected)

        # the np.nansum version should be same as Series.sum version
        pairs_series = pairwise(nandf, lambda x, y: x.sum() - y.sum(), 
                         order=True, force_values=False)
        tm.assert_frame_equal(pairs, pairs_series)

    def test_dshift_float(self):
        """
        Since float is nan-able. The simple call should give the 
        same output
        """
        test = df.dshift(1)
        correct = df.shift(1)
        tm.assert_almost_equal(test.values, correct.values)

        test = df.dshift(-2)
        correct = df.shift(-2)
        tm.assert_almost_equal(test.values, correct.values)

    def test_dshift_bool(self):
        """
        bool has no nan.
        """
        bf = df > 0
        test = bf.dshift(1)
        correct = bf.shift(1).fillna(False).astype(bool)
        assert test.dtypes.unique()[0] == bool
        assert test.dtypes.nunique() == 1
        tm.assert_almost_equal(test.values, correct.values)

        test = bf.dshift(-2)
        correct = bf.shift(-2).fillna(False).astype(bool)
        assert test.dtypes.unique()[0] == bool
        assert test.dtypes.nunique() == 1
        tm.assert_almost_equal(test.values, correct.values)

    def test_dshift_int(self):
        """
        int has no nan.
        """
        intdf = (df * 100).astype(int)
        test = intdf.dshift(1)
        correct = intdf.shift(1).fillna(-1).astype(int)
        assert test.dtypes.unique()[0] == int
        assert test.dtypes.nunique() == 1
        tm.assert_almost_equal(test.values, correct.values)

        test = intdf.dshift(-2)
        correct = intdf.shift(-2).fillna(-1).astype(int)
        assert test.dtypes.unique()[0] == int
        assert test.dtypes.nunique() == 1
        tm.assert_almost_equal(test.values, correct.values)

    def test_dshift_raw(self):
        # bool
        bf = df > 0
        test = bf.dshift(1, raw=True)
        correct = bf.shift(1).fillna(False).astype(float)
        assert type(test) is np.ndarray
        tm.assert_almost_equal(test, correct.values)

        # float
        test = df.dshift(1, raw=True)
        correct = df.shift(1)
        assert type(test) is np.ndarray
        tm.assert_almost_equal(test, correct.values)

    def test_dshift_fill_value(self):
        # float
        test = df.dshift(1, fill_value=-100)
        correct = df.shift(1).fillna(-100)
        tm.assert_almost_equal(test.values, correct.values)

        # int
        intdf = (df * 100).astype(int)
        test = intdf.dshift(1, fill_value=-100)
        correct = intdf.shift(1).fillna(-100)
        tm.assert_almost_equal(test.values, correct.values)

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
