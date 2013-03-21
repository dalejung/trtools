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

class TestHDFFile(TestCase):
    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_directory_meta(self):
        """
            Moved HDFFile to directoryl. Test that meta is workihng
        """
        with TemporaryDirectory() as td:
            store = tb.HDFFile(td + '/test', 'w', type='directory')
            store['AAPL'] = df
            store.handle.meta('testtest', 123)
            store.table.meta('testtest', 456)
            store.close()

            # reload
            store = tb.HDFFile(td + '/test')
            assert store.handle.meta('testtest') == 123
            assert store.table.meta('testtest') == 456

class TestOBTFile(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_directory_meta(self):
        """
            Moved OBT to default to directory format. Test the the meta is working
        """
        with TemporaryDirectory() as td:
            store = tb.OBTFile(td + '/test', 'w', 'symbol', type='directory')
            store['AAPL'] = df
            store.handle.meta('testtest', 123)
            store.obt.meta('testtest', 456)
            store.close()

            # reload
            store = tb.OBTFile(td + '/test')
            assert store.handle.meta('testtest') == 123
            assert store.obt.meta('testtest') == 456

    def test_tuple_frame_key(self):
        """
            Moved OBT to default to directory format. Test the the meta is working
        """
        with TemporaryDirectory() as td:
            store = tb.OBTFile(td + '/test', 'w', 'symbol', type='directory')
            store[('AAPL', 5902)] = df
            store.close()

            # reload
            store = tb.OBTFile(td + '/test')

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
