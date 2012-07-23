import collections
import datetime

from pandas import DataFrame, Series, TimeSeries

from trtools.monkey import patch, patch_prop

def date_attr(date):
    return date.year, date.month, date.day

class TimeSelector(object):
    def __init__(self, obj, func):
        self.obj = obj
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(self.obj, *args, **kwargs)

    def __eq__(self, other):
        if not isinstance(other, collections.Sequence) or isinstance(other, basestring):
            other = (other,)

        return self(*other)

def select_date(obj, year, month=None, day=None):
    if isinstance(year, datetime.datetime):
        year, month, day = date_attr(year)

    if day is None and month is None:
        return obj.select(lambda x: x.year == year)
    if day is None and month is not None:
        return obj.select(lambda x: x.year == year and x.month == month)
    return obj.select(lambda x: x.date() == datetime.date(year, month, day))

class TimeIndexer(object):
    def __init__(self, obj):
        self.obj = obj
        self.date = TimeSelector(obj, select_date)

    def pluck(self, year, month, day, offset=3):
        return self.obj.pluck(datetime.datetime(year, month, day), offset)

@patch_prop([DataFrame, Series, TimeSeries], 'ts')
def ts(self):
    return TimeIndexer(self)
