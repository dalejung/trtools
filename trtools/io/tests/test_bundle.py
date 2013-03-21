from unittest import TestCase

import pandas as pd
import numpy as np

import trtools.io.bundle as b
import trtools.util.testing as tm
from trtools.util.tempdir import TemporaryDirectory

# panel with many items and < 10 columns
panel = pd.Panel({('item'+str(i), i, i+.0324) : tm.fake_ohlc() for i in range(5000)})
panel.items = pd.MultiIndex.from_tuples(panel.items)
assert isinstance(panel.items, pd.MultiIndex) # make this more complicated

class TestBundle(TestCase):
    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_panel(self):
        """
        Overview test that panel bundle saving works
        """
        with TemporaryDirectory() as td:
            b.save_panel(panel, td)

            test = b.load_panel(td)
            tm.assert_panel_equal(panel, test)

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
