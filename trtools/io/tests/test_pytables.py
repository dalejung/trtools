from unittest import TestCase

import pandas as pd
import numpy as np

import trtools.io.api as tb
import trtools.util.testing as tm
from trtools.util.tempdir import TemporaryDirectory

ind = pd.DatetimeIndex(start="2000-01-01", freq="30min", periods=300)
df = pd.DataFrame({
    'high': np.random.randn(len(ind)),
    'low': np.random.randn(len(ind)),
    'open': np.random.randn(len(ind)),
    'other_dates' : ind
}, index=ind)
df.index.name = 'timestamp'

class TestPyTables(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_convert_frame(self):
        desc, recs, types = tb.convert_frame(df)
        dtype_msg = "{0} does not match dtype. \nExpected: {1}\nGot: {2}"

        # test floats
        for col in ['high', 'low', 'open']:
            assert df[col].dtype == desc[col].dtype, dtype_msg.format(col, df[col].dtype, desc[col].dtype)

        # test datetime / pytable represents as ints
        col = 'other_dates'
        assert df[col].dtype.type == np.datetime64
        assert desc[col].dtype == int


if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
