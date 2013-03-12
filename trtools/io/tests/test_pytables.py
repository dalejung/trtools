from unittest import TestCase

import pandas as pd
import numpy as np

import trtools.io.api as tb
import trtools.util.testing as tm
from trtools.util.tempdir import TemporaryDirectory

ind = pd.DatetimeIndex(start="2000-01-01", freq="30min", periods=300)
df = pd.DataFrame({
    'open': np.random.randn(len(ind)),
    'high': np.random.randn(len(ind)),
    'low': np.random.randn(len(ind)),
    'close': np.random.randn(len(ind)),
    'vol': np.random.randn(len(ind)),
    'other_dates' : ind
}, index=ind)
df = df.reindex(columns=['open', 'high', 'low', 'close', 'vol', 'other_dates'])
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
        for col in ['open', 'high', 'low', 'close']:
            assert df[col].dtype == desc[col].dtype, dtype_msg.format(col, df[col].dtype, desc[col].dtype)

        # test datetime / pytable represents as ints
        col = 'other_dates'
        assert df[col].dtype.type == np.datetime64
        assert desc[col].dtype == int

    def test_append_table(self):
        with TemporaryDirectory() as td:
            store = tb.OBTFile(td+'/test.h5', 'w', 'symbol')
            store['AAPL'] = df

            # Pytable table
            table = store.obt.table.obj
            colnames = table.colnames
            # index name, columns, frame_key
            assert colnames == ['timestamp', 'open', 'high', 'low', 'close', 'vol', 'other_dates', 'symbol']

            temp = store.ix['AAPL']
            tm.assert_frame_equal(temp, df, "dataframe returned from HDF is different", check_names=False)

            # this shoudl throw error
            bad_df = df.reindex(columns=['high', 'low', 'open', 'close', 'other_dates', 'vol'])
            try:
                store['BAD'] = bad_df
            except tb.MismatchColumnsError as e:
                pass # success
            else:
                assert False, 'this should return an error, columns in wrong order'

            # fails when obt doesn't check column order. stored wrong
            temp = store.ix['BAD']
            if len(temp): 
                # if properly throwing erros, we should never reach here
                tm.assert_frame_equal(temp, df, "dataframe returned from HDF is different")



if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
