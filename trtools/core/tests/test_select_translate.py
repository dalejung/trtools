from unittest import TestCase

import numpy as np
import pandas as pd
import trtools.core.select_translate as sl


class TestSelectTranslate(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_select_translate(self):
        """
            Test the dictionary translate
        """
        df = pd.DataFrame({111: [1,2], 123: [3,4]})

        # setup the translation
        sl.KEY_TRANS = {'dale': 111, 'bob': 123}

        # non list columns should return a scalar
        test = df.ix[0, 'dale']
        assert np.isscalar(test)
        assert test == 1

        # list columns should return a series
        test = df.ix[0, ['dale']]
        assert isinstance(test, pd.Series)
        # use values since we have int-index
        assert test.values[0] == 1


        # multiple selection
        test = df.ix[0, ['dale', 'bob']]
        assert isinstance(test, pd.Series)
        # use values since we have int-index
        assert test.values[0] == 1
        assert test.values[1] == 3

        # multi row
        test = df.ix[:, ['dale', 'bob']]
        assert isinstance(test, pd.DataFrame)
        assert np.all(test.values[0] == [1,3])
        assert np.all(test.values[1] == [2,4])

        # unset the translation so future tests don't mess up
        sl.KEY_TRANS = {}

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
