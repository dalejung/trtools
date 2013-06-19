from unittest import TestCase

import pandas as pd
import pandas.util.testing as tm
import numpy as np

import trtools.core.topper as topper
reload(topper)

arr = np.random.randn(10000)
s = pd.Series(arr)

class TestTopper(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_topn_largest(self):
        # get the n largest
        bn_res = topper.bn_topn(arr, 10)
        assert bn_res[-1] == max(arr) # sanity check
        pd_res = s.order()[-10:]
        tm.assert_almost_equal(bn_res, pd_res)

        # change result to biggest to smallest
        bn_res = topper.bn_topn(arr, 10, ascending=False)
        assert bn_res[0] == max(arr) # sanity check
        pd_res = s.order(ascending=False)[:10] # grab from end since we reversed
        tm.assert_almost_equal(bn_res, pd_res)


    def test_top_smallest(self):
        # get the nsmallest
        bn_res = topper.bn_topn(arr, -10)
        assert bn_res[0] == min(arr) # sanity check
        pd_res = s.order()[:10]
        tm.assert_almost_equal(bn_res, pd_res)

        # change result to biggest to smallest
        bn_res = topper.bn_topn(arr, 10, ascending=False)
        bn_res = topper.bn_topn(arr, -10, ascending=False)
        assert bn_res[-1] == min(arr) # sanity check
        pd_res = s.order(ascending=False)[-10:] # grab from end since we reversed
        tm.assert_almost_equal(bn_res, pd_res)

    def test_top_arg(self):
        # get the nlargest
        bn_res = topper.bn_topn(arr, 10)
        bn_args = topper.bn_topargn(arr, 10)
        arg_res = arr[bn_args]
        tm.assert_almost_equal(bn_res, arg_res)

        # get the nsmallest
        bn_res = topper.bn_topn(arr, -10)
        bn_args = topper.bn_topargn(arr, -10)
        arg_res = arr[bn_args]
        tm.assert_almost_equal(bn_res, arg_res)

        # get the nsmallest
        bn_res = topper.bn_topn(arr, -10, ascending=False)
        bn_args = topper.bn_topargn(arr, -10, ascending=False)
        arg_res = arr[bn_args]
        tm.assert_almost_equal(bn_res, arg_res)

    def test_nans(self):
        """
        bottleneck.partsort doesn't handle nans. We need to correct for them.

        the arg version is trickiers since we need to make sure to 
        translate back into the nan-filled array
        """
        nanarr = np.arange(10).astype(float)
        nanarr[nanarr % 2 == 0] = np.nan

        test = topper.topn(nanarr, 3)
        correct = [5,7,9]
        tm.assert_almost_equal(test, correct)

        test = topper.topn(nanarr, -3)
        correct = [1,3,5]
        tm.assert_almost_equal(test, correct)

        test = topper.topargn(nanarr, 3)
        correct = [5,7,9]
        tm.assert_almost_equal(test, correct)

        test = topper.topargn(nanarr, -3)
        correct = [1,3,5]
        tm.assert_almost_equal(test, correct)

        test = topper.topargn(nanarr, -3, ascending=False)
        correct = [5,3,1]
        tm.assert_almost_equal(test, correct)

if __name__ == '__main__':
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
