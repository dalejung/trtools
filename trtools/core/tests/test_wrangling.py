from unittest import TestCase

import pandas as pd
import numpy as np

import trtools.core.wrangling as wrangling
import trtools.util.testing as tm
pairwise = wrangling.pairwise

df = pd.DataFrame(index=range(10))
for x in range(3):
    df[x] = range(x, x+10)

nandf = df.copy().astype(float)
nandf.ix[9:,1] = np.nan

class TestWrangling(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_pairwise(self):
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


if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
