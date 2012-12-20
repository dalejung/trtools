from unittest import TestCase
import collections

import pandas as pd
import numpy as np

import trtools.util.testing as tm
import trtools.core.column_panel as column_panel
ColumnPanel = column_panel.ColumnPanel
ColumnPanelMapper = column_panel.ColumnPanelMapper
ColumnPanelGroupBy = column_panel.ColumnPanelGroupBy

import trtools.monkey as monkey
import trtools.tools.tile # .tile monkey patch


class TestColumnPanel(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_df_map_attrproxy(self):
        """
            Test that 
        """
        df = pd.DataFrame({'test':range(5), 
                           'strings':['bob', 'dale', 't', '123', 'frank']})
        data = {'df1':df, 'df2':df}
        cp = column_panel.ColumnPanel(data)
        assert isinstance(cp.dtypes, monkey.AttrProxy)
        cp_dtypes = cp.dtypes.tail()
        # note, I would have used assert_frame_equal but dtype is getting converted to 
        # object when creating a panel
        assert isinstance(cp_dtypes, pd.DataFrame)
        assert cp_dtypes.shape == (2, 2)
        assert np.all(cp_dtypes.columns == ['df1', 'df2'])
        assert np.all(cp_dtypes.index == ['strings', 'test'])

    def test_columnpanel_groupby(self):
        """
            Test wrapping the panel groupby with ColumnPanelGroupBy
        """
        N = 10000
        data = {}
        data['AAPL'] = tm.fake_ohlc(N)
        data['AMD'] = tm.fake_ohlc(N)
        data['INTC'] = tm.fake_ohlc(N)
        cp = ColumnPanel(data)

        ds = cp.dataset()
        ds['log_returns'] = np.log(1+cp.close.pct_change())
        ds['close'] = cp.close

        # make sure to get the panelgroupby
        grouped = ds.to_panel().downsample('MS', label='left', closed='left')
        cpgrouped = ColumnPanelGroupBy(grouped)
        # check if meaned is equal
        cmean = grouped.mean()
        test_mean = cpgrouped.process(lambda df: df.mean())
        tm.assert_panel_equal(cmean, test_mean)

        bins = [-1, 0, 1]

        # 12-19-12 errors. 
        # problem is that downsample returns a PanelGroupBy which doesn't have the 
        # delegate and combine logic.
        test_tiled = cpgrouped.process(lambda df: df.tile(bins, 'log_returns').mean())
        correct = grouped.process(
            lambda df: ColumnPanelMapper(df).tile(bins, 'log_returns').mean())

        # this implicitly checks that inputs are panel4d
        tm.assert_panel4d_equal(test_tiled, correct)

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
