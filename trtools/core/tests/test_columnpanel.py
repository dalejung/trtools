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

from trtools.util.tempdir import TemporaryDirectory


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
        df = pd.DataFrame({'test':list(range(5)), 
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

    def test_bundle_io(self):
        """
            Test saving bundle io. 
        """
        N = 10000
        data = {}
        data['AAPL'] = tm.fake_ohlc(N)
        data['AMD'] = tm.fake_ohlc(N).tail(100)
        data['INTC'] = tm.fake_ohlc(N).head(100)
        cp = ColumnPanel(data)

        with TemporaryDirectory() as td:
            path = td + 'TEST.columnpanel'
            cp.bundle_save(path)

            loaded = cp.bundle_load(path)
            tm.assert_columnpanel_equal(cp, loaded)

    def test_df_ix_single(self):
        """
        Test single row ix. Shoudl return a dataframe
        """
        ind = pd.date_range(start="2000-01-01", freq="D", periods=5)
        df = pd.DataFrame({'test':list(range(5)), 
                           'strings':['bob', 'dale', 't', '123', 'frank']}, index=ind)
        data = {'df1':df, 'df2':df}
        cp = column_panel.ColumnPanel(data)
        test = cp.ix[0]
        assert test.df1['strings'] == 'bob'
        assert test.df2['strings'] == 'bob'
        assert test.df1['test'] == 0
        assert test.df2['test'] == 0

        test = cp.ix[ind[0]]
        assert test.df1['strings'] == 'bob'
        assert test.df2['strings'] == 'bob'
        assert test.df1['test'] == 0
        assert test.df2['test'] == 0
    
    def test_column_index(self):
        """
        Test that the column is returned as a pandas Index
        """
        ind = pd.date_range(start="2000-01-01", freq="D", periods=5)
        df = pd.DataFrame({'test':list(range(5)), 
                           'strings':['bob', 'dale', 't', '123', 'frank']}, index=ind)
        data = {'df1':df, 'df2':df}
        cp = column_panel.ColumnPanel(data)
        assert isinstance(cp.columns, pd.Index)
        assert cp.columns.equals(pd.Index(['strings', 'test']))
        # test column cache
        old_id = id(cp.columns)
        assert old_id == id(cp.columns), "Should returned cached columns"
        # create new col from old col
        cp['test_col'] = cp.test
        assert isinstance(cp.columns, pd.Index)
        assert cp.columns.equals(pd.Index(['strings', 'test', 'test_col'])) # did cache update?

    def test_dropitems(self):
        """
        Test that CP.dropitems drops empty frames
        """
        ind = pd.date_range(start="2000-01-01", freq="D", periods=5)
        df = pd.DataFrame({'test':list(range(5)), 
                           'strings':['bob', 'dale', 't', '123', 'frank']}, index=ind)
        data = {'df1':df, 'df2':df.iloc[:3]} # note that df2 has ONLY the first 3 rows, rest NA
        cp = column_panel.ColumnPanel(data)

        test = cp.tail(2)
        assert cp.items == ['df1', 'df2']

        test = cp.tail(2).dropitems()
        assert test.items == ['df1'], 'dropitems should have dropped df2'

        # tail(3) has a one-row df2
        test = cp.tail(3).dropitems()
        assert test.items == ['df1', 'df2']
        df2 = test.im['df2']
        assert np.all(df2.count() == 1), 'df2 has only one non-na row'


if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
