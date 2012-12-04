from unittest import TestCase

import pandas as pd
import pandas.util.testing as tm
import numpy as np

import trtools.core.binning as binning
reload(binning)

zscore = lambda x: (x - x.mean()) / x.std()

class TestBinning(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_apply_put_frame(self):
        ind = pd.DatetimeIndex(start="2000-01-01", freq="5min", periods=1000)
        df = pd.DataFrame({'open': np.random.randn(len(ind)), 
                           'close': np.random.randn(len(ind))}, index=ind)
        grouper = df.downsample('D').grouper

        t1 = df.downsample('D').transform(zscore)
        t2 = binning.apply_put_frame(df, grouper, zscore)
        tm.assert_frame_equal(t1, t2)

        # test apply_put by col
        topen = binning.apply_put(df, grouper, {'open':zscore})
        assert len(topen.columns) == 1
        tm.assert_series_equal(t2['open'], topen['open'])

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
