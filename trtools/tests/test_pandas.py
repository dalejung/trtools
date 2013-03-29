from unittest import TestCase
import collections

import pandas as pd 
import numpy as np

ind = pd.date_range(start="1990/01/01", freq="H", periods=1000)
df = pd.DataFrame(index=ind)
df['open'] = np.random.randn(len(ind))
df['high'] = np.random.randn(len(ind))
df['low'] = np.random.randn(len(ind))
df['close'] = np.random.randn(len(ind))

ohlc = collections.OrderedDict()
ohlc['open'] = 'first'
ohlc['high'] = 'max'
ohlc['low'] = 'min'
ohlc['close'] = 'last'

class TestPandas(TestCase):
    # testing base pandas

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_groupby_order(self):
        # https://github.com/pydata/pandas/issues/2455
        grouped = df.groupby(lambda x: x.date())
        daily = grouped.agg(ohlc)
        assert np.all(df.columns == daily.columns)

    def test_panelgroupby(self):
        def agg_func(pan):
            assert isinstance(pan, pd.Panel)
            return pan.mean()

        ind = pd.date_range('1/1/2000', periods=100)
        data = np.random.randn(2,len(ind),4)
        wp = pd.Panel(data, items=['Item1', 'Item2'], major_axis=ind, minor_axis=['A', 'B', 'C', 'D'])

        from pandas.tseries.resample import TimeGrouper
        #timegrouper
        tg = TimeGrouper('M', axis=1)
        grouper = tg.get_grouper(wp)
        bingrouped = wp.groupby(grouper)
        # Failed 12-15-12
        # https://github.com/pydata/pandas/issues/2537
        bingrouped.agg(agg_func)

    def test_multindex_dtype_promotion(self):
        """
        Creating a multindex is promoting floats to object
        """
        # https://github.com/pydata/pandas/issues/3211
        lev1 = np.arange(10)
        lev2 = np.linspace(0, 9, 10)
        mi = pd.MultiIndex.from_arrays([lev1, lev2])

        # ints work fine
        assert lev1.dtype == mi.levels[0].dtype

        # failure
        assert lev2.dtype == mi.levels[1].dtype


if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
