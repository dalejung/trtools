import sys
import collections

import numpy as np
from pandas import Series, Panel, DataFrame
from pandas.util import py3compat

def _iter_or_slice(key):
    if isinstance(key, slice):
        return key
    if isinstance(key, basestring):
        return [key]
    if not isinstance(key, collections.Iterable): 
        return [key]
    return key

class PanelDict(dict):
    def __repr__(self):
        return repr(Series(self.keys()))

class ColumnPanelItems(object):
    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        for k in self.obj.frames:
            if k == key:
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

class ColumnPanel(object):
    def __init__(self, obj=None, name=None):
        self.frames = {}
        self.columns = []
        self.im = ColumnPanelItems(self)
        if isinstance(obj, dict):
            self._init_dict(obj)
        if isinstance(obj, Panel):
            self._init_panel(obj)
        if isinstance(obj, DataFrame):
            self._init_dataframe(obj, name)

        self._cache = {}

    def _init_dict(self, data):
        first = next(data.itervalues())
        self.columns = list(first.columns)
        for name, df in data.iteritems():
            self.frames[name] = df

    def _init_panel(self, panel):
        self.columns = list(panel._get_axis('minor'))
        for name, df in panel.iteritems():
            self.frames[name] = df

    def _init_dataframe(self, df, name=None):
        name = name or df.name
        self.columns = [name]
        if name is None:
            raise Exception('need a name for df')

        for col, series in df.iteritems():
            frame = DataFrame({name:series}, name=col)
            self.frames[col] = frame

    @property
    def items(self):
        return self.frames.keys()

    def __setitem__(self, key, value):
        self.columns.append(key)
        for name, df in self.frames.iteritems():
            df[key] = value[name]

        if key in self._cache:
            del self._cache[key]

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return self._getitem_tuple(key)

        if key not in self.columns:
            raise Exception('%s :Column does not exist'% key)
        return self._gather_column(key)

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
        for key in items:
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

        df = DataFrame(results, name=key)
        self._cache[key] = df
        return df
        return TRDataFrame(df)

    def to_panel(self):
        copies = {}
        for k,v in self.frames.iteritems():
            copies[k] = v.copy()
        return Panel(copies)

    def __repr__(self):
        item_keys = self.frames.keys()
        lengths = len(self.columns), len(self.items)
        dims = "Dimensions: {0} Columns x {1} Items".format(*lengths)
        items = 'Items: %s to %s' % (item_keys[0], item_keys[-1])
        columns = 'Columns axis: %s to %s' % (self.columns[0], self.columns[-1])
        output = 'ColumnPanel: \n%s\n%s\n%s' % (dims, items, columns)
        return output

    def __getstate__(self): 
        d = {}
        d['frames'] = self.frames
        d['columns'] = self.columns
        return d

    def __setstate__(self, d): 
        self.__dict__.update(d)
        self.__dict__['im'] = ColumnPanelItems(self)

# IPYTYHON
def install_ipython_completers():  # pragma: no cover
    """Register the DataFrame type with IPython's tab completion machinery, so
    that it knows about accessing column names as attributes."""
    from IPython.utils.generics import complete_object

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
if "IPython" in sys.modules:  # pragma: no cover
    try: 
        install_ipython_completers()
    except Exception:
        pass 
