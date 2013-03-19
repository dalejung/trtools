import os.path
from collections import OrderedDict, Iterable
import operator

import numpy as np
from pandas import Series, Panel, DataFrame, Panel4D
import pandas as pd

import trtools.io.api as trio

import trtools.monkey as monkey

def _iter_or_slice(key):
    if isinstance(key, slice):
        return key
    if isinstance(key, basestring):
        return [key]
    if not isinstance(key, Iterable): 
        return [key]
    return key

class PanelDict(OrderedDict):
    """
        This started off as a quick way to have dict.__repr__ not spit 
        out a ton of stuff
    """
    def __init__(self):
        super(PanelDict, self).__init__()

    def __repr__(self):
        return repr(Series(self.keys()))

    def __getattr__(self, key):
        try:
            return super(PanelDict, self).__getattr__(key)
        except:
            # not sure what the best way to handle this is.
            # OrderedDict.__init__ use try/catch to initialize self..__root
            # removing this results in recursion error
            if key == '_OrderedDict__root':
                raise

        test = next(self.itervalues())
        func = getattr(test, key, None)
        if func is None:
            return super(PanelDict, self).__getattr__(key)
        if callable(func):
            return _wrap(self, key)
        else: 
            return monkey.AttrProxy(key, test, lambda _, key: _wrap(self, key))

def apply_cp(self, func, *args, **kwargs):
    """
        apply func to each frame and wrap
        based on return
    """
    data = PanelDict() 
    for key, df in self.iteritems():
        data[key] = func(df, *args, **kwargs)

    if len(data) == 0:
        return 

    data = _box_items(data)
    return data

def _box_items(data):
    test = data[data.keys()[0]]
    if isinstance(test, ColumnPanel):
        data = OrderedDict([(k, v.to_panel()) for k, v  in data.iteritems()])
        return Panel4D(data)
    if isinstance(test, Panel):
        return Panel4D(data)
    if isinstance(test, DataFrame):
        return ColumnPanel(data)
    if isinstance(test, Series):
        return DataFrame(data)
    return data

def _wrap(obj, key):
    """
        Wraps a attr-key into an apply_cp call
    """
    getter = operator.attrgetter(key) # supports nested attrs
    def wrapped(*args, **kwargs):
        return apply_cp(obj, lambda df: getter(df)(*args, **kwargs))
    return wrapped

class ColumnPanelMapper(object):
    """
        Exposes methods on ColumnPanel.frames items.
    """
    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        _, test = next(self.obj.iteritems())
        func = getattr(test, key, None)
        if func is None:
            raise AttributeError("{0} not a method".format(key))
        if callable(func) and not isinstance(func, monkey.AttrNameSpace):
            return self._wrap(key)
        else: 
            return monkey.AttrProxy(key, test, lambda _, key: self._wrap(key))

    def _wrap(self, key):
        obj = self.obj
        return _wrap(obj, key)

class ColumnPanelGroupBy(object):
    def __init__(self, grouped):
        self.grouped = grouped

    def __getattr__(self, key):
        if hasattr(self.grouped, key):
            return getattr(self.grouped, key)
        # TODO 
        # Add a wrap func for Panel and DataFrame method
        raise AttributeError()

    def process(self, func, *args, **kwargs):
        # wrap each subset with a PanelMapper

        # TODO
        # here's the thing, What if I dont' want ColumnPanelMapper?
        # what if I want a Panel specific thing?
        wrapped = lambda df: func(ColumnPanelMapper(df))
        res = self.grouped.process(wrapped, *args, **kwargs)
        return res

class ColumnPanelItems(object):
    """
        Class for .im item access

        cp.im.AAPL 
    """
    def __init__(self, obj):
        self.obj = obj
        self.lookup_cache = {}

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        # shortcircuit lookupcache
        k = self.lookup_cache.get(key)
        if k:
            return self.obj.frames[k]

        for k in self.obj.frames:
            if k == key:
                self.lookup_cache[key] = k
                return self.obj.frames[k]
        raise AttributeError("{0} is not an item in ColumnPanel".format(key))

class TRDataFrame(object):
    def __init__(self, df):
        self.df = df

    def __getattr__(self, key):
        try:
            return self.df[key]
        except:
            pass

        try:
            return getattr(self.df, key)
        except:
            raise AttributeError("StockPanel or Panel does not have this attr")

    def __getitem__(self, key):
        """
            This is different because we are supporting objects as keys. 
            Some keys might match both a basestring and int. The `in` keyword
            will match by hash so can only match one type.
        """
        columns = self.df.columns
        where = np.where(columns == key)[0]
        ind = where[0]
        key = columns[ind]
        df = self.df[key] 
        return df

    def __repr__(self):
        return repr(self.df)

    def __array__(self):
        return self.df.__array__()

class ColumnPanelIndexer(object):
    """
        Remember, this is REPLICATING the DataFrame.ix
        So that means it can't restrict the items
    """
    def __init__(self, obj):
        self.obj = obj

    def __getitem__(self, key):
        """
            Trying to replicate df.ix for Column Panel. 
            ix[index, col, items]
        """
        if isinstance(key, tuple):
            return dispatch_ix(self.obj, key)

        if hasattr(key, 'dtypes') and np.all(key.dtypes == bool):
            return mask(self.obj, key)

        if isinstance(key, slice):
            return dispatch_ix(self.obj, key)

        return dispatch_ix(self.obj, key)

    def __setitem__(self, key, val):
        self.obj[key] = val

def dispatch_ix(self, key):
    """
        Essentially call ix[key] for each dataframe and return new
        ColumnPanel
    """
    data = OrderedDict()

    for k, df in self.frames.iteritems():
        data[k] = df.ix[key]

    test = data[self.frames.keys()[0]]
    if isinstance(test, pd.DataFrame):
        return ColumnPanel(data) 
    if isinstance(test, pd.Series):
        return pd.DataFrame(data)

def mask(self, index):
    """
        Take a bool index and return a column panel
        with False rows set to None. 

        This is to replicate df.ix[df.col > 0]

        If index is a series, it will apply to all frames. 
        If index is a DataFrame, it's assumed that each col
        will correspond to a ColumnPanel.frames item. 
    """
    data = OrderedDict()

    m = index   
    for key, val in self.frames.iteritems():
        if index.ndim > 1:
            m = index[key]
        val = na_promote(val.copy())
        val.ix[~m] = None
        data[key] = val
    return ColumnPanel(data) 

def na_promote(df):
    """ Make dataframe na promotable. Convert ints to float dtypes """
    for k, dtype in df.dtypes.iteritems():
        if dtype == int:
            df[k] = df[k].astype(float)

    return df

class ColumnPanel(object):
    def __init__(self, obj=None, name=None):
        self._columns = []
        self.im = ColumnPanelItems(self)
        self.df_map = ColumnPanelMapper(self)

        if isinstance(obj, dict):
            self._init_dict(obj)
        if isinstance(obj, Panel):
            self._init_panel(obj)
        if isinstance(obj, DataFrame):
            self._init_dataframe(obj, name)

        self._cache = {}

    _frames = None
    _panel = None
    @property
    def frames(self):
        """
            Until the frames is accessed. The ColumnPanel
            acts like a quasi Panel, keeping the Panel instance around. 
            This is to save processing when we're just using ColumnPanel as an
            intermediatry step
        """
        if self._frames is None:
            self._frames = OrderedDict()
            if self._panel is not None:
                for name, df in self._panel.iteritems():
                    self._frames[name] = df
                    self._panel = None
        return self._frames

    _col_cache = None
    @property
    def columns(self):
        if self._col_cache is None:
            self._col_cache = pd.Index(self._columns)
        return self._col_cache

    def _init_dict(self, data):
        # just aligning indexes
        panel = Panel(data)
        self._init_panel(panel)

    def _init_panel(self, panel):
        self._columns = list(panel._get_axis('minor'))
        self._col_cache = None
        self._panel = panel

    def _init_dataframe(self, df, name=None):
        name = name or df.name
        self._columns = [name]
        self._col_cache = None
        if name is None:
            raise Exception('need a name for df')

        for col, series in df.iteritems():
            frame = DataFrame({name:series})
            frame.name = col
            self.frames[col] = frame

    def dataset(self):
        """
            Create an empty ColumnPanel with the same items
            and index
        """
        data = OrderedDict()
        for key, val in self.frames.iteritems():
            data[key] = DataFrame(index=val.index)
        return ColumnPanel(data)

    _ix = None
    @property
    def ix(self):
        if self._ix is None:
            self._ix = ColumnPanelIndexer(self)
        return self._ix

    @property
    def index(self):
        """
            Optimally, all frames should share same index. 
            Test a couple and then return if same. Not sure how to handle
            non equal indexes.
        """
        import random
        sample_size = min(len(self.frames), 3)
        tests = random.sample(self.items, sample_size)
        indexes = [self.frames[key].index for key in tests]
        index = indexes[0]
        try:
            for ind in indexes[1:]:
                if not np.all(index == ind):
                    raise
        except:
            raise Exception("Indexes are not equal")

        return index

    @property
    def items(self):
        return self.frames.keys()

    def foreach(self, func, *args, **kwargs):
        return apply_cp(self, func, *args, **kwargs)

    def __setitem__(self, key, value):
        self._columns.append(key)
        self._col_cache = None
        for name, df in self.frames.iteritems():
            df[key] = value[name]

        if key in self._cache:
            del self._cache[key]

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return self._getitem_tuple(key)

        if key in self._columns:
            return self._gather_column(key)
        try:
            return self.df_map[key]
        except:
            pass

        raise Exception('%s: Column does not exist'% key)

    def _getitem_tuple(self, keys):
        """
            panel[cols, items]

            returns ColumnPanel
        """
        cols, items = keys
        cols = _iter_or_slice(cols)
        items = _iter_or_slice(items)
        if isinstance(items, slice):
            items = self.items
        data = {}

        # Need to match on eq() and not hash
        keys = self.frames.keys()
        for key in keys:
            if key in items:
                df = self.frames[key]
                data[key] = df.ix[:, cols]

        return ColumnPanel(data)

    def _getitem_items(self, items):
        data = {}
        for key in items:
            data[key] = self.frames[key]

        return ColumnPanel(data)

    def _gather_column(self, key):
        if key in self._cache:
            return self._cache[key]

        results = {}
        for name, df in self.frames.iteritems():
            results[name] = df[key]

        df = DataFrame(results)
        df.name = key
        self._cache[key] = df
        return df

    def to_panel(self):
        if self._panel is not None:
            return self._panel

        copies = {}
        for k,v in self.frames.iteritems():
            copies[k] = v.copy()
        return Panel(copies)

    def __repr__(self):
        item_keys = self.frames.keys()
        lengths = len(self.columns), len(self.items)
        dims = "Dimensions: {0} Columns x {1} Items".format(*lengths)
        items = 'Items: %s to %s' % (item_keys[0], item_keys[-1])
        if len(self.columns) > 0:
            columns = 'Columns axis: %s to %s' % (self.columns[0], self.columns[-1])
        else:
            columns = "Columns axis: 0 cols"
        output = 'ColumnPanel: \n%s\n%s\n%s' % (dims, items, columns)
        return output

    def __iter__(self):
        return self.iteritems()

    def iteritems(self):
        return self.frames.iteritems()

    def downsample(self, freq, closed=None, label=None, axis=None):
        panel = self.to_panel()
        grouped = panel.downsample(freq=freq, closed=closed, label=label, axis=axis)
        grouped = ColumnPanelGroupBy(grouped)
        return grouped

    def sample(self, N=10, axis='items'):
        """
            Grab a random sample

            Example usage:
                cp.ix["2000"].sample(3)
                Grabs 3 non empty frames from the year 2000

        """
        import random
        if axis == 'items':
            keys = self.items[:]

        random.shuffle(keys)
        data = {}
        for k in keys:
            df = self.frames[k]
            if df.count().sum() == 0:
                continue
            data[k] = df
            if len(data) >= N:
                break

        return ColumnPanel(data)

    def __getstate__(self): 
        d = {}
        d['frames'] = self.frames
        d['columns'] = self._columns
        return d

    def __setstate__(self, d): 
        self.__dict__.update(d)
        self.__dict__['im'] = ColumnPanelItems(self)

    def bundle_save(self, path, frame_key='frame_key'):
        """ 
        """
        filepath = trio.bundle_filepath(path)
        store = trio.OBTFile(filepath, 'w', frame_key=frame_key, type='directory')
        try:
            for key, frame in self.frames.items():
                # helpful if key is an object
                if hasattr(key, frame_key):
                    key = getattr(key, frame_key)
                store[key] = frame
        except:
            store.close()
            # delete on error, don't store half complete save
            self.delete(filepath)
            raise IOError()
        else:
            store.close()

    def bundle_load(self, path):
        filepath = trio.bundle_filepath(path)
        store = trio.OBTFile(filepath)
        try:
            df = store.obt.ix[:]
            panel = df.to_panel()
            panel = panel.swapaxes('minor', 'items')
            # convert csinums to stock objects
            return ColumnPanel(panel)
        finally:
            store.close()

# IPYTYHON
def install_ipython_completers():  # pragma: no cover
    """Register the DataFrame type with IPython's tab completion machinery, so
    that it knows about accessing column names as attributes."""
    from IPython.utils.generics import complete_object
    from pandas.util import py3compat

    @complete_object.when_type(ColumnPanel)
    def complete_column_panel(obj, prev_completions):
        return prev_completions + [c for c in obj.columns \
                    if isinstance(c, basestring) and py3compat.isidentifier(c)]                                          
    @complete_object.when_type(ColumnPanelItems)
    def complete_column_panel_items(obj, prev_completions):
        return prev_completions + [c for c in obj.obj.frames.keys() \
                    if isinstance(c, basestring) and py3compat.isidentifier(c)]                                          

# Importing IPython brings in about 200 modules, so we want to avoid it unless
# we're in IPython (when those modules are loaded anyway).
import sys
if "IPython" in sys.modules:  # pragma: no cover
    try: 
        install_ipython_completers()
    except Exception:
        pass 
