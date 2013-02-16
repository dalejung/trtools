from unittest import TestCase

import pandas as pd
import trtools.util.testing as tm

import trtools.tools.list_frame as lf

class TestObject(object):
    _frame_cols = ('timestamp', 'id', 'data')
    def __init__(self, timestamp, id, data, *args, **kwargs):
        self.id = id
        self.data = data
        self.timestamp = timestamp

class TestObjectFrame(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_empty_eventlist(self):
        """
        Start from empty eventlist and append
        """
        ind = pd.date_range(start="2000/1/1", periods=10)

        events = [TestObject(ind[i], i, len(ind)-i) for i in range(len(ind))]
        el = lf.ListFrame()
        for evt in events:
            el.append(evt)

        df = el.to_frame()
        for i, evt in enumerate(el):
            assert evt.data == df.ix[i]['data']
            assert evt.timestamp == df.ix[i]['timestamp']
            assert evt.id == df.ix[i]['id']

    def test_to_frame(self):
        """
            Test creating DataFrame and modifying
        """
        ind = pd.date_range(start="2000/1/1", periods=10)

        events = [TestObject(ind[i], i, len(ind)-i) for i in range(len(ind))]
        el = lf.ListFrame(events)
        df = el.to_frame()
        assert el._cache_df is df
        assert len(df) == len(events)
        assert df.ix[9]['data'] == el[9].data
        for i, evt in enumerate(el):
            assert evt.data == df.ix[i]['data']
            assert evt.timestamp == df.ix[i]['timestamp']
            assert evt.id == df.ix[i]['id']

        # modify list
        del el[3]
        assert el._cache_df is None
        df = el.to_frame()
        assert el._cache_df is df
        assert len(df) == len(el)
        for i, evt in enumerate(el):
            assert evt.data == df.ix[i]['data']
            assert evt.timestamp == df.ix[i]['timestamp']
            assert evt.id == df.ix[i]['id']

        el.pop()
        el.pop()
        el.pop()
        assert len(el.to_frame()) == 6, "1 del + 3 pops should be 6 llft"
        assert el.to_frame().ix[5]['id'] == 6 # note, we took off last 3 and fourth

    def test_attrs(self):
        """
            Test passing in attrs to init
        """
        ind = pd.date_range(start="2000/1/1", periods=10)

        events = [TestObject(ind[i], i, len(ind)-i) for i in range(len(ind))]
        el = lf.ListFrame(events, attrs=['id'])
        df = el.to_frame()
        assert len(df.columns) == 1
        assert df.columns[0] == 'id'
        tm.assert_series_equal(df['id'], pd.Series(range(10)))

    def test_repr_col(self):
        """
        Test that repr col works correctly
        """
        ind = pd.date_range(start="2000/1/1", periods=10)

        events = [TestObject(ind[i], i, len(ind)-i) for i in range(len(ind))]
        el = lf.ListFrame(events, attrs=['id'], repr_col=True)
        df = el.to_frame()
        for i, evt in enumerate(events):
            assert repr(evt) == df.repr[i]

    def test_to_frame_override(self):
        """
            Test to_frame(attrs, repr_col)
        """
        ind = pd.date_range(start="2000/1/1", periods=10)

        events = [TestObject(ind[i], i, len(ind)-i) for i in range(len(ind))]
        el = lf.ListFrame(events, attrs=['id'], repr_col=True)
        correct = el.to_frame()

        el2 = lf.ListFrame(events)
        bad = el2.to_frame() # regular ole to_frame
        assert set(bad.columns) == set(TestObject._frame_cols)
        test = el2.to_frame(attrs=['id'], repr_col=True)
        tm.assert_frame_equal(test, correct)

    def test_tuple_attr(self):
        """
            Added the ability to add a tuple attr which is (col, attr) and 
            attr can be a func
        """
        ind = pd.date_range(start="2000/1/1", periods=10)

        events = [TestObject(ind[i], i, len(ind)-i) for i in range(len(ind))]
        el = lf.ListFrame(events, attrs=['timestamp', 'id', 
                                         # note the lambda for bob
                                          ('bob', lambda x: id(x))])
        df = el.to_frame()
        for i, evt in enumerate(events):
            assert id(evt) == df.bob[i]

if __name__ == '__main__':
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-s','-x','--pdb', '--pdb-failure'],exit=False)   
