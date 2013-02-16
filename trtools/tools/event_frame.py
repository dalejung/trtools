"""
    Set of tools to translate between a list of events and DataFrames
"""
from collections import OrderedDict
from operator import attrgetter
import pandas as pd
import functools

def _getter(evt, attr):
    """ essentially attrgetter that returns None when attr does not exist """
    _get = attrgetter(attr)
    try:
        return _get(evt)
    except:
        return None

def _column_picker(attr, events):
    """ Grab an attr for every Event in list """
    getter = attr
    if not callable(getter):
        getter = functools.partial(_getter, attr=attr)
    data = map(getter, events)
    return data

def _process_attrs(attrs):
    """
        Normalize attrs into the form of [(col, attr), (col, attr)]
    """
    new_attrs = OrderedDict()
    for attr in attrs:
        col = attr
        if isinstance(attr, tuple):
            col, attr = attr
        # special cases
        if attr == 'class_name':
            attr = '__class__.__name__'
        if attr == 'repr':
            attr = repr
        new_attrs[col] = attr

    return new_attrs

def eventlist_to_frame(lst, attrs=None, repr_col=False):
    if len(lst) == 0:
        return pd.DataFrame()

    # grab first event to get attrs, assumes homogenity
    test = lst[0]
    if attrs is None:
        attrs = test.repr_attrs

    # TODO: Make it so we remove the attrs that we've already outputed.
    # if we assume non-homogenity, we have to remove diferent attrs per
    # event type
    if repr_col:
        attrs.append('repr')
    attrs = _process_attrs(attrs)

    sdict = OrderedDict()
    for col, attr in attrs.items():
        data = _column_picker(attr, lst)
        sdict[col] = data


    return pd.DataFrame(sdict)

class EventList(list):
    _cache_df = None

    def __init__(self, data=None, attrs=None, repr_col=False):
        if data is None:
            data = [] # meh
        self.attrs = attrs
        self.repr_col = repr_col
        super(EventList, self).__init__(data)

    def to_frame(self, attrs=None, repr_col=None):
        if attrs is None:
            attrs = self.attrs
        if repr_col is None:
            repr_col = self.repr_col

        # turned off caching for now. Need to cache key by attrs and repr_col
        #if self._cache_df is None:
        self._cache_df = eventlist_to_frame(self, attrs, repr_col)
        return self._cache_df

    mutation_methods = [
        'append', 
        '__setitem__', 
        '__delitem__',
        'sort', 
        'extend',
        'insert',
        'pop',
        'remove',
        'reverse',
    ]

# alter mutation methods to clear the cached_df
def _binder(method):
    def _method(self, *args, **kwargs):
        self._cache_df = None
        sup = super(EventList, self)
        getattr(sup, method)(*args, **kwargs)
    return _method

for method in EventList.mutation_methods:
    setattr(EventList, method, _binder(method))
