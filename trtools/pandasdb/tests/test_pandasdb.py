from unittest import TestCase
import cPickle as pickle

import pandas as pd

import trtools.pdtools.pandasdb as pddb
import trtools.util.testing as tm

class TestPandasTable(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_create(self):
        df = pd.DataFrame({'test':range(10)})
        table = pddb.PandasTable('test')
        table.init_df(df)

    def test_get_fp(self):
        table = pddb.PandasTable('test')
        fp = table._get_fp()
        fp.close()
        assert fp.mode == 'rb'

    def test_init_df(self):
        df = pd.DataFrame({'test':range(10)})
        table = pddb.PandasTable('test')
        table.init_df(df)

        assert df is table._df

        data = tm.TestStringIO(pickle.dumps(df))

        table = pddb.PandasTable('test')
        table.init_df(data)
        assert tm.assert_almost_equal(df, table._df)

    def test__save(self):
        df = pd.DataFrame({'test':range(10)})
        table = pddb.PandasTable('test')
        table.init_df(df)

        data = tm.TestStringIO()
        table.save(data)

        data.seek(0)
        new_table = pickle.loads(data.read())
        assert tm.assert_almost_equal(new_table._df, df)
        data.free()


if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
