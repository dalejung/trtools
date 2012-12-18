from unittest import TestCase

import pandas as pd
import pandas.util.testing as tm
import numpy as np

import trtools.core.column_panel as column_panel
import trtools.monkey as monkey

df = pd.DataFrame({'test':range(5), 'strings':['bob', 'dale', 't', '123', 'frank']})
data = {'df1':df, 'df2':df}
cp = column_panel.ColumnPanel(data)

class TestColumnPanel(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_df_map_attrproxy(self):
        assert isinstance(cp.dtypes, monkey.AttrProxy)
        cp_dtypes = cp.dtypes.tail()
        # note, I would have used assert_frame_equal but dtype is getting converted to 
        # object when creating a panel
        assert isinstance(cp_dtypes, pd.DataFrame)
        assert cp_dtypes.shape == (2, 2)
        assert np.all(cp_dtypes.columns == ['df1', 'df2'])
        assert np.all(cp_dtypes.index == ['strings', 'test'])

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
