from unittest import TestCase
import os.path

import os

import pandas as pd
import numpy as np
from rpy2.robjects import r
from rpy2.robjects.vectors import SexpVector, ListVector, StrSexpVector

import trtools.util.testing as tm

import trtools.rpy.conversion as conv

# Make sure to set R_HOME in environ

def curpath():
    pth, _ = os.path.split(os.path.abspath(__file__))
    return pth

class TestConversion(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_dataframe(self):
        ind = pd.date_range(start='1/1/2002', end='12/30/2008', freq="30min")

        # test converting a dataframe with 1 col. This errored while
        # multiple columns worked fine
        df = pd.DataFrame({'returns': np.random.randn(len(ind))}, index=ind)
        conv.convert_df_to_xts(df)


        # test with two columns
        df['bob'] = 3
        conv.convert_df_to_xts(df)

    def test_convert_datetime(self):
        ind = pd.date_range(start='1/1/2002', end='12/30/2008', freq="30min")
        ri = conv.convert_datetime_index_num(ind)
        tm.assert_almost_equal(ri[0], ind.asi8[0] / 1E9)

        assert ri.do_slot('tzone')[0] == 'UTC'

        # convert back to datetime
        conv_dates = pd.Series(np.array(ri)).astype(np.dtype('M8[s]'))
        tm.assert_almost_equal(conv_dates, ind)

    def test_convert_posixct_to_index(self):
        ind = pd.date_range(start='1/1/2002', end='12/30/2008', freq="30min")
        ri = conv.convert_datetime_index_num(ind)

        # test converting back 'UTC'
        dt = conv.convert_posixct_to_index(ri)
        tm.assert_almost_equal(dt.values, ind.values)

        # test 'US/Eastern'
        # At one point this failed due to DatetimeIndex being 
        # given a tz. DatetimeIndex needs to be initialied to UTC
        # and then converted
        ri.do_slot_assign('tzone', StrSexpVector(['US/Eastern']))
        dt = conv.convert_posixct_to_index(ri)
        assert dt.tz.zone == 'US/Eastern'
        assert ind.tz is None
        tm.assert_almost_equal(dt.values, ind.values)

        ind = ind.tz_localize('UTC')
        est_ind = ind.tz_convert('US/Eastern')
        est_ri = conv.convert_datetime_index_num(est_ind)
        assert est_ri.do_slot('tzone')[0] == 'US/Eastern'
        est_dt = conv.convert_posixct_to_index(est_ri)
        tm.assert_almost_equal(est_dt, est_ind)
        assert est_dt.tz.zone == 'US/Eastern'


if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
