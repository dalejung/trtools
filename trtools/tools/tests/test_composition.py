from unittest import TestCase
import os.path

import pandas as pd
import numpy as np

import trtools.util.testing as tm
import trtools.tools.composition as composition
UserSeries = composition.UserSeries
UserFrame = composition.UserFrame

def curpath():
    pth, _ = os.path.split(os.path.abspath(__file__))
    return pth

class SubFrame(UserFrame):
    def resample(self):
        return 'test'

class TestComposition(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_user_series(self):
        s = pd.Series(range(1, 10), index=range(11, 20))
        us = UserSeries(s)
        tm.assert_series_equal(s, us)

        def assert_op(pobj, userobj, op):
            return
            cls = type(userobj)
            correct = op(pobj)
            test = op(userobj)
            assert isinstance(test, cls)
            if isinstance(correct, pd.Series):
                tm.assert_series_equal(correct, test)
            if isinstance(correct, pd.DataFrame):
                tm.assert_frame_equal(correct, test)

        assert_op(s, us, lambda s: s.pct_change())
        assert_op(s, us, lambda s: s + 19)
        assert_op(s, us, lambda s: s / 19)
        assert_op(s, us, lambda s: np.log(s))
        assert_op(s, us, lambda s: np.log(s))
        assert_op(s, us, lambda s: np.diff(s))

        bools = us > 5
        tvals = np.repeat(1, len(us))
        fvals = np.repeat(0, len(us))
        wh = np.where(bools, tvals, fvals)
        assert wh.pobj is not None
        assert wh.dtype == int
        tm.assert_series_equal(wh, bools.astype(int))

    def test_us_view(self):    
        s = pd.Series(range(0, 10), index=range(10, 20))
        us = s.view(UserSeries)
        tm.assert_series_equal(s, us)

        arr = np.array(range(10))
        arrs = pd.Series(arr)
        arrus = arr.view(UserSeries)
        tm.assert_series_equal(arrs, arrus)

    def test_datetime_us_view(self):    
        data = range(0, 10)
        ind = pd.date_range(start="1/1/2000", freq="D", periods=len(data))
        s = pd.Series(data, index=ind)
        us = s.view(UserSeries)
        tm.assert_series_equal(s, us)

        arr = np.array(range(10))
        arrs = pd.Series(arr)
        arrus = arr.view(UserSeries)
        tm.assert_series_equal(arrs, arrus)

        us.view(UserSeries)

    def test_userframe(self):
        import trtools.core.dataset as dataset# instlal monkey patch
        df = pd.DataFrame(np.random.randn(10, 5))
        df = UserFrame(df)
        ds = df.dataset()
        # 12-27-12 FAIL. Really should only rewrap pd.DataFrame
        assert isinstance(ds, dataset.DataSet)

    def test_subframe(self):
        pass
df = pd.DataFrame(np.random.randn(10, 5))
sub = SubFrame(df)


if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
