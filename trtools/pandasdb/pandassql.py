import operator

import pandas as pd
import numpy as np

def combine_filters(filters, df=None, op=operator.and_):
    """
        combine will convert all filters to bool arrays then use
        reduce. 

        Since FilterGroup's reduce calls combine_filters, this will 
        progress recursively.
    """
    processed_filters = [to_bool(filter, df) for filter in filters]
    return reduce(lambda a,b: op(a,b), processed_filters)

def to_bool(obj, df):
    if isinstance(obj, pd.Series):
        return obj
    if isinstance(obj, FilterGroup):
        return obj.reduce(df)

def convert_keyword_filters(df, filters):
    """
    """
    flist = []
    for filter in filters:
        if isinstance(filter, tuple):
            col, value, op = filter
            filter = op(df[col], value)
        flist.append(filter)
    return flist

class FilterGroup(object):
    def __init__(self, filters=None, type="AND"):
        self.type = type
        filters = filters or []
        self.filters = filters

    def reduce(self, df=None):
        op = self.type == 'AND' and operator.and_ or operator.or_
        filters = convert_keyword_filters(df, self.filters)
        return combine_filters(filters, op=op)

    def add_filter(self, filter):
        self.filters.append(filter)

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
        if len(filters) > 0:
            combined_filter = combine_filters(filters, self.df)
            ret = self.df[combined_filter]

        if cols is not None and len(cols) > 0:
            ret = ret.xs(cols, axis=1)

        if len(joins) > 0:
            for target, on in joins:
                ret = pd.merge(ret, target, on=on)

        return ret

    def __getattr__(self, name):
        if name in self.df.columns:
            return PandasColumn(self, name)
        raise AttributeError(name)

    def __getstate__(self): return self.__dict__
    def __setstate__(self, d): self.__dict__.update(d)

    def filter(self, *args, **kwargs):
        return self.query().filter(*args, **kwargs)

    def filter_or(self, *args, **kwargs):
        return self.query().filter_or(*args, **kwargs)

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

    def isin(self, other):
        filter = self.db.df[self.column].isin(other)
        return self.db.execute(filters=[filter])

    def notin(self, other):
        filter = self.db.df[self.column].isin(other) # same as isin
        filter = ~filter
        return self.db.execute(filters=[filter])

    def __mod__(self, other):
        # uses pandas contains
        filter = self.db.df[self.column].str.contains(other)
        res = self.db.execute(filters=[filter])
        return res

    def between(self, left, right):
        col = self.db.df[self.column]
        filter = (col >= left) & (col <= right)
        res = self.db.execute(filters=[filter])
        return res

    def __call__(self, other, op=operator.eq):
        return self.column_filter(other, op)

    def __getattr__(self, key):

        # TODO this behavior of wrapping objects recursively happens a lot. Should find
        # a sane way to standardize this. 

        column = self.db.df[self.column]
        if hasattr(column, key):
            attr = getattr(column, key)
            if callable(attr):
                attr = self._wrap(attr)
            return attr

        # str methods
        if hasattr(column.str, key):
            attr = getattr(column.str, key)
            if callable(attr):
                attr = self._wrap(attr)
            return attr

        raise AttributeError()

    def _wrap(self, func):
        def wrapped(*args, **kwargs):
            res = func(*args, **kwargs)
            if isinstance(res, np.ndarray) and probably_bool(res):
                return self.db.execute(filters=[res.fillna(False)])
            return res
        return wrapped

def probably_bool(arr):
    """ dumb test for bool arrays that ahve nans """
    s = pd.Series(arr)
    counts = s.value_counts()
    keys = counts.keys()
    for key in keys:
        if not isinstance(key, bool) and not isinstance(key, np.bool_):
            return False
    return True

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

    def filter_list(self, args, kwargs):
        flist = []
        flist.extend(args)

        for k, value in kwargs.items():
            if not isinstance(value, list):
                value = [value]
            for v in value:
                flist.append((k, v, operator.eq))

        return flist

    def filter_by(self, *args, **kwargs):
        filters = self.filters[:]

        flist = self.filter_list(args, kwargs)

        fg = FilterGroup(flist, type='AND')
        filters.append(fg)
        return Query(self.db, self.cols, filters, self.joins)

    filter = filter_by

    def filter_or(self, *args, **kwargs):
        filters = self.filters[:]

        flist = self.filter_list(args, kwargs)

        fg = FilterGroup(flist, type="OR")
        filters.append(fg)
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
        raise AttributeError(key)

    def join(self, target, on=None):
        joins = self.joins[:]
        joins.append((target, on))
        return Query(self.db, self.cols, self.filters, joins)

# monkey patch
pd.DataFrame.sql = property(lambda x: PandasSQL(x))
