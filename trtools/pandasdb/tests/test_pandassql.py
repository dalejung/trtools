from unittest import TestCase

import numpy as np
import pandas as pd
import pandas.util.testing as tm
import trtools.pandasdb.api as pandassql

class TestPandasDB(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        df = pd.DataFrame({'dale':range(10), 'bob':range(10, 20)})
        df['names'] = ['dale', 'dane', 'donna', 'mike', 'miller'] * 2
        db = pandassql.PandasSQL(df)
        assert db.df is df
        self.db = db

    def test_pandas_sql(self):
        db = self.db
        q = db.query()
        assert q.db is db
        assert q.cols is None

        q = db.query('dale')
        assert q.db is db
        assert q.cols == ['dale']

    def test_full_all(self):
        db = self.db
        res = db.query().all()
        assert tm.assert_almost_equal(db.df.values, res.values)


    def test_sql_filter(self):
        db = self.db
        q = db.query()

        res = q.filter_by(db.df.dale < 3).all()
        exp = db.df[db.df.dale < 3]
        tm.assert_frame_equal(res, exp)

        res = q.filter_by(db.df.names == 'dale').all()
        exp = db.df[db.df.names == 'dale']
        tm.assert_frame_equal(res, exp)

    def test_sql_chain_filter(self):
        """
            test using multiple filter_by
        """
        db = self.db
        q = db.query()

        res = q.filter_by(db.df.dale < 7).filter_by(db.df.bob > 12).all()
        exp = db.df[(db.df.dale < 7) & (db.df.bob > 12)]
        tm.assert_frame_equal(res, exp)

    def test_sql_filter_args(self):
        db = self.db
        q = db.query()

        res = q.filter_by(db.df.dale < 7, db.df.bob > 12).all()
        exp = db.df[(db.df.dale < 7) & (db.df.bob > 12)]
        tm.assert_frame_equal(res, exp)

    def test_sql_filter_args_OR(self):
        db = self.db
        q = db.query()

        res = q.filter_or(db.df.dale < 7, db.df.bob > 12).all()
        exp = db.df[(db.df.dale < 7) | (db.df.bob > 12)]
        tm.assert_frame_equal(res, exp)

    def test_sql_filter_kwargs(self):
        db = self.db
        q = db.query()

        res = q.filter_by(names='dale').all()
        exp = db.df[db.df.names == 'dale']
        tm.assert_frame_equal(res, exp)

        # multiple
        res = q.filter_by(names='dale', bob=10).all()
        exp = db.df[(db.df.names == 'dale') & (db.df.bob == 10)]
        tm.assert_frame_equal(res, exp)

    def test_sql_filter_kwargs_OR(self):
        db = self.db
        q = db.query()

        res = q.filter_or(names=['dale','dane']).all()
        exp = db.df[(db.df.names == 'dale') | (db.df.names == 'dane')]
        tm.assert_frame_equal(res, exp)

        # multiple
        res = q.filter_or(names='dale', bob=[10, 13]).all()
        exp = db.df[(db.df.names == 'dale') | (db.df.bob == 10) | (db.df.bob == 13)]
        tm.assert_frame_equal(res, exp)

    def test_col_startswith(self):
        db = self.db
        ret = db.names.startswith('mi')
        assert tm.assert_almost_equal(ret.index, pd.Series([3,4,8,9]))

        ret = db.names.startswith('dal')
        assert tm.assert_almost_equal(ret.index, pd.Series([0,5]))

    def test_slice(self):
        """
            Using a slice will execute the query and return the dataset
        """
        db = self.db
        res = db.query()[:5]
        exp = db.query().all()[:5]
        assert tm.assert_almost_equal(res.values, exp.values)

        # test single
        res = db.query().ix[5]
        exp = db.query().all().ix[5]
        assert tm.assert_almost_equal(res, exp)

    def test_query_getattr(self):
        db = self.db
        res = db.query().sum()
        exp = db.query().all().sum()
        assert tm.assert_almost_equal(res, exp)
        assert res['dale'] == sum(db.df.dale)

    def test_query_cols(self):
        df = self.db.df
        df.sql.query('dale').filter_by(df.dale == 3).all()


    def test_query_join(self):
        df = pd.DataFrame({'a':range(10), 'b':range(10,20)})
        df2 = pd.DataFrame({'a':range(10), 'c':range(20,30), 'd':range(30,40)})
        res = df.sql.query().join(df2.xs(['a', 'c'], axis=1), 'a').all()
        exp = pd.DataFrame({'a':range(10), 'b':range(10,20), 'c': range(20,30)})
        assert tm.assert_almost_equal(res.values, exp.values)

class TestFilterGroup(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_simple(self):
        f = pandassql.FilterGroup()
        b1 = pd.Series([0,1,1,1,0])
        b2 = pd.Series([0,1,1,1,0])
        f.add_filter(b1)
        f.add_filter(b2)
        res = f.reduce()
        assert tm.assert_almost_equal(res, b1)

    def test_simple_and(self):
        f = pandassql.FilterGroup()
        b1 = pd.Series([0,1,1,1,0])
        b2 = pd.Series([0,1,0,0,0])
        f.add_filter(b1)
        f.add_filter(b2)
        res = f.reduce()
        exp = pd.Series([0,1,0,0,0])
        assert tm.assert_almost_equal(res, exp)

    def test_simple_or(self):
        f = pandassql.FilterGroup(type="OR")
        b1 = pd.Series([0,1,0,1,0])
        b2 = pd.Series([1,1,0,0,0])
        f.add_filter(b1)
        f.add_filter(b2)
        res = f.reduce()
        exp = pd.Series([1,1,0,1,0])
        assert tm.assert_almost_equal(res, exp)

    def test_nested(self):
        f = pandassql.FilterGroup(type="OR")
        b1 = pd.Series([0,1,0,1,0])
        b2 = pd.Series([1,1,0,0,0])
        f.add_filter(b1)
        f.add_filter(b2)

        parent = pandassql.FilterGroup(type="AND")
        b3 = pd.Series([1,0,0,1,0])
        parent.add_filter(b3)
        parent.add_filter(f)

        res = parent.reduce()

        assert tm.assert_almost_equal(res, b3)

        sup = pandassql.FilterGroup(type="OR")
        b4 = pd.Series([1,1,0,0,1])
        sup.add_filter(parent)
        sup.add_filter(b4)

        res = sup.reduce()

        assert tm.assert_almost_equal(res, pd.Series([1,1,0,1,1]))

class TestPandasSQL(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_series_sql(self):
        s = pd.Series(range(10)).astype(float)
        s[3] = np.nan
        assert pd.isnull(s[3])
        assert s.sql.isnull().index[0] == 3

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)
