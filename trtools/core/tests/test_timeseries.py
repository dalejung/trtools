from unittest import TestCase

import pandas as pd
from pandas.core.groupby import BinGrouper
import trtools.util.testing as tm
import numpy as np

import trtools.core.timeseries as ts

# start on friday, so second day is saturday
df = tm.fake_ohlc(1000000, freq="5min", start="2000-01-07")
# business days and trading hours
df = df.ix[df.index.dayofweek < 5]
df = ts.trading_hours(df)

class TestBinning(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_downsample(self):
        # these should be equivalent
        grouped = df.downsample('D', drop_empty=False)
        test = grouped.mean()
        correct = df.resample('D', how='mean')
        tm.assert_frame_equal(test, correct)

    def test_downsample_drop_empty(self):
        """
        the drop_empty which is the default will not include
        empty groups into the GroupBy.
        """
        grouped = df.downsample('D')
        test = grouped.mean()
        correct = df.resample('D', how='mean').dropna(how='all')
        tm.assert_frame_equal(test, correct)

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)
