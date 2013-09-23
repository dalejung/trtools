from unittest import TestCase

import numpy as np
import pandas as pd
import trtools.util.testing as tm
import trtools.core.select_translate as sl


class TestSelectTranslate(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_select_translate_frame(self):
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

        # test boolean index
        test = df.ix[:, [True, False]]
        col = df.columns[0] # not guaranteed column order so grab it this way
        assert np.all(df.ix[:, [col]].values == test.values)

        # unset the translation so future tests don't mess up
        sl.KEY_TRANS = {}

    def test_select_translate_panel(self):
        """
            Test the dictionary translate
        """
        df1 = tm.makeTimeDataFrame()
        df2 = tm.makeTimeDataFrame()
        df3 = tm.makeTimeDataFrame()
        panel = pd.Panel({111: df1, 123: df2, 666:df3})

        # setup the translation
        sl.KEY_TRANS = {'dale': 111, 'bob': 123}
        test = panel.ix["dale"]
        tm.assert_frame_equal(test, df1)
        tm.assert_frame_equal(panel.ix[123], df2)
        tm.assert_frame_equal(panel.ix['bob'], df2)
        tm.assert_frame_equal(panel.ix['bob', :10], df2.ix[:10])
        tm.assert_frame_equal(panel.ix['bob', :10, :3], df2.ix[:10, :3])
        # grab sub panel
        test = panel.ix[["dale", "bob"]]
        assert np.all(test.items == [111, 123])
        tm.assert_frame_equal(test.ix['dale'], df1)
        tm.assert_frame_equal(test.ix['bob'], df2)

        sl.KEY_TRANS = None


if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
