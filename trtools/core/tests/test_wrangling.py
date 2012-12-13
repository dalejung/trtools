from unittest import TestCase

import pandas as pd

import trtools.core.wrangling as wrangling
import trtools.util.testing as tm
pairwise = wrangling.pairwise

df = pd.DataFrame(index=range(100))
for x in range(3):
    df[x] = range(x, x+100)

class TestWrangling(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_pairwise(self):
        # test with order=True
        # test with permutations
        pairs = pairwise(df, lambda x, y: x.sum() - y.sum())
        expected = pd.DataFrame([[0, -100, -200], 
                                 [100, 0, -100],
                                 [200, 100, 0]], index=range(3), dtype=float)
        tm.assert_frame_equal(pairs, expected)

        # test with combinations
        pairs = pairwise(df, lambda x, y: x.sum() - y.sum(), order=False)
        expected = pd.DataFrame([[0, -100, -200], 
                                 [-100, 0, -100],
                                 [-200, -100, 0]], index=range(3), dtype=float)
        tm.assert_frame_equal(pairs, expected)

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
