from unittest import TestCase
import collections

import pandas as pd 
import numpy as np

import trtools.tools.composition as composition
import trtools.core.dataset as dataset

reload(dataset)

ind = pd.date_range(start="1/1/2000", freq="D", periods=100)
df = pd.DataFrame({'test':np.arange(len(ind))}, index=ind)

class TestDataSet(TestCase):
    # testing base pandas

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_dataset(self):
        ds = dataset.DataSet(index=ind)
        s = composition.UserSeries(1, index=ind)
        s.bob = 'hi'
        s.zz = 'zz'
        s.name = 'bee'
        ds['dale'] = s
        assert isinstance(ds.dale, composition.UserSeries)
        assert ds.dale.bob == 'hi'
        assert ds.dale.zz == 'zz'

        s.zz = 'zz2'
        ds['dale'] = s
        assert ds.dale.zz == 'zz2'

        ds['whee'] = 123
        assert np.all(ds.whee == 123)

    def test_dataset_monkey(self):
        ds = df.dataset()
        assert np.all(ds.index == ind)

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
