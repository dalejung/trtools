from unittest import TestCase

import pandas as pd
import pandas.util.testing as tm
import trtools.pandas.pandasdb as pandasdb

class TestPandasDB(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        df = pd.DataFrame({'dale':range(10), 'bob':range(10, 20)})
        df['names'] = ['dale', 'dane', 'donna', 'mike', 'miller'] * 2
        db = pandasdb.PandasSQL(df)
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
        assert tm.assert_almost_equal(db.df, res)


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
        assert tm.assert_almost_equal(res, exp)

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


if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
