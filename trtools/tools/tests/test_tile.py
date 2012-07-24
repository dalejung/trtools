from unittest import TestCase

import numpy as np
import pandas as pd

import trtools.tools.tile as tile

class TestTile(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_base_tile(self):
        arr = np.arange(10)
        data = pd.Series(arr)
        bins = [0, 5, 10]
        ret = tile.tile(data, bins, infinite=False)
        ranges = ret.groups.keys()
        counts = ret.count()
        correct = {}
        correct[0] = 5
        correct[5] = 4
        for r in ranges:
            assert correct[r.l] == counts[r]

    def test_na_tile(self):
        """
            Test where bins don't give full coverage
        """
        correct = {}
        correct[0] = 5
        correct[5] = 4

        arr = np.arange(10)
        data = pd.Series(arr)
        bins = [0, 5]
        ret = tile.tile(data, bins, infinite=False)
        ranges = ret.groups.keys()
        counts = ret.count()
        for r in ranges:
            assert correct[r.l] == counts[r]

    def test_inf_tile(self):
        """ Support for [-inf, first] and [last, inf] """
        correct = {}
        correct[-tile.inf] = 1
        correct[2] = 2
        correct[4] = 6

        arr = np.arange(10)
        data = pd.Series(arr)
        bins = [2, 4]
        ret = tile.tile(data, bins)
        ranges = ret.groups.keys()

        # verify infs exist
        lower_bounds = [r.l for r in ranges]
        for k,v in correct.items():
            assert k in lower_bounds

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],
                  exit=False)   
