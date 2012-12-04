from unittest import TestCase
import os.path
import cPickle as pickle
from trtools.util.tempdir import TemporaryDirectory

import pandas as pd

import trtools.pandasdb.api as pddb
import trtools.util.testing as tm

class TestPandasTable(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_create(self):
        with TemporaryDirectory() as td:
            filepath = os.path.join(td, 'test')
            df = pd.DataFrame({'test':range(10)})
            table = pddb.PandasTable(filepath)
            table._init_df(df)

    def test_get_fp(self):
        with TemporaryDirectory() as td:
            filepath = os.path.join(td, 'test')
            with open(filepath, 'w') as f:
                f.write('\0')
            table = pddb.PandasTable(filepath)
            fp = table._get_fp()
            fp.close()
            assert fp.mode == 'rb'

    def test_init_df(self):
        with TemporaryDirectory() as td:
            filepath = os.path.join(td, 'test')
            df = pd.DataFrame({'test':range(10)})
            table = pddb.PandasTable(filepath)
            table.init_df(df)

            assert df is table._df

            data = tm.TestStringIO(pickle.dumps(df))

            table = pddb.PandasTable(filepath)
            table._init_df(data)
            assert tm.assert_almost_equal(df, table._df)

    def test_save(self):
        with TemporaryDirectory() as td:
            filepath = os.path.join(td, 'test')

            df = pd.DataFrame({'test':range(10)})
            table = pddb.PandasTable(filepath)
            table._init_df(df)

            # save to string
            data = tm.TestStringIO()
            table.save(data)

            # PandasTable saves as df
            data.seek(0)
            new_table = pickle.loads(data.read())
            assert tm.assert_almost_equal(new_table, df)
            data.free()

            # save to disk
            table.save()
            pandas_table = pddb.PandasTable(filepath)
            assert tm.assert_almost_equal(pandas_table._df, df)


if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
