import operator

import pandas as pd

def combine_filters(filters):
    return reduce(lambda a,b: a & b, filters)

class PandasSQL(object):
    def __init__(self, df):
        self.df = df

    def query(self, *args):
        # tuple is treated as one key
        # need list
        cols = list(args) or None
        return Query(self, cols)

    def execute_query_all(self, query):
        cols = query.cols
        filters = query.filters
        order_by = query.order_by
        joins = query.joins
        return self.execute(cols, filters, order_by, joins)

    def execute(self, cols=None, filters=[], order_by=[], joins=[]):
        ret = self.df
        if cols is not None and len(cols) > 0:
            ret = ret.xs(cols, axis=1)
        if len(filters) > 0:
            combined_filter = combine_filters(filters)
            ret = ret[combined_filter]

        if len(joins) > 0:
            for target, on in joins:
                ret = pd.merge(ret, target, on=on)

        return ret

    def __getattr__(self, attr):
        if attr in self.df.columns:
            return PandasColumn(self, attr)

    def __getstate__(self): return self.__dict__
    def __setstate__(self, d): self.__dict__.update(d)

class PandasColumn(object):
    """
        Designed for quick column queries

        db.col == val
        db.col.startswith(str)
    """
    def __init__(self, db, column):
        self.db = db
        self.column = column

    def column_filter(self, other, op):
        filter = op(self.db.df[self.column],other)
        return self.db.execute(filters=[filter])

    def __eq__(self, other):
        return self.column_filter(other, operator.eq)

    def __ne__(self, other):
        return self.column_filter(other, operator.ne)

    def __gt__(self, other):
        return self.column_filter(other, operator.gt)

    def __ge__(self, other):
        return self.column_filter(other, operator.ge)

    def __lt__(self, other):
        return self.column_filter(other, operator.lt)

    def __le__(self, other):
        return self.column_filter(other, operator.le)

    def __imod__(self, other):
        #TODO replace with a like or re matching func
        return self.startswith(other)

    def startswith(self, other):
        func = lambda x: x.startswith(other)
        return self.column_filter(func, pd.Series.apply)


class Query(object):
    """
        Query object modeled after sqlalchemy.

        db.query().filter_by(bool_array).all()
    """
    def __init__(self, db, cols, filters=None, joins=None):
        self.db = db
        self.cols = cols
        self.filters = filters or []
        self.joins = joins or []
        self.order_by = None 

    def filter_by(self, filter):
        filters = self.filters[:]
        filters.append(filter)
        return Query(self.db, self.cols, filters, self.joins)

    def all(self):
        return self.db.execute_query_all(self)

    def __getitem__(self, item):
        res = self.all()[item]
        return res

    def __getattr__(self, key):
        # if attr exists on DataFrame, execute query and return attr
        # from resulting df
        if hasattr(pd.DataFrame, key):
            return getattr(self.all(), key)

    def join(self, target, on=None):
        joins = self.joins[:]
        joins.append((target, on))
        return Query(self.db, self.cols, self.filters, joins)

# monkey patch
pd.DataFrame.sql = property(lambda x: PandasSQL(x))
