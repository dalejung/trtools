import warnings
from collections import OrderedDict
from datetime import time

import tables as tb
import pandas as pd
import pandas.lib as lib
import numpy as np
import pandas.io.pytables as pdtables

from trtools.compat import izip, pickle
from trtools.io.common import _filename
from trtools.io.table_indexing import create_slices

MIN_ITEMSIZE = 10

class MismatchColumnsError(Exception):
    pass

def convert_frame(df):
    """
        Input: DataFrame
        Output: pytable table description and pytable compatible recarray
    """
    sdict = OrderedDict()
    atoms = OrderedDict()
    types = OrderedDict()

    #index
    index_name = df.index.name or 'pd_index'
    converted, inferred_type, atom = _convert_obj(df.index)
    atoms[index_name] = atom
    sdict[index_name] = converted
    types[index_name] = inferred_type


    # columns
    for col in df.columns:
        converted, inferred_type, atom = _convert_obj(df[col])
        atoms[col] = atom
        sdict[col] = converted
        types[col] = inferred_type

    # create table desc
    desc = OrderedDict() 
    for pos, data in enumerate(atoms.items()):
        k, atom = data
        col = tb.Col.from_atom(atom, pos=pos) 
        desc[str(k)] = col

    # create recarray
    dtypes = [(str(k), v.dtype) for k, v in list(sdict.items())]
    recs = np.recarray(shape=len(df), dtype=dtypes)
    for k, v in list(sdict.items()):
        recs[str(k)] = v
    return desc, recs, types

def _convert_obj(obj):
    """
        Convert a series to pytables values and Atom
    """
    if isinstance(obj, pd.DatetimeIndex):
        converted = obj.asi8
        return converted, 'datetime64', tb.Int64Atom()
    elif isinstance(obj, pd.PeriodIndex):
        converted = obj.values
        return converted, 'periodindex', tb.Int64Atom()
    elif isinstance(obj, pd.PeriodIndex):
        converted = obj.values
        return converted, 'int64', tb.Int64Atom()

    inferred_type = lib.infer_dtype(obj)
    values = np.asarray(obj)

    if inferred_type == 'datetime64':
        converted = values.view('i8')
        return converted, inferred_type, tb.Int64Atom()
    if inferred_type == 'string':
        # TODO, am I doing this right?
        converted = np.array(list(values), dtype=np.bytes_)
        itemsize = converted.dtype.itemsize
        # for OBT, can't assume value will be right for future
        # frame keys
        if itemsize < MIN_ITEMSIZE:
            itemsize = MIN_ITEMSIZE
            converted = converted.astype("S{0}".format(itemsize))

        return converted, inferred_type, tb.StringAtom(itemsize)
    elif inferred_type == 'unicode':
        # table's don't seem to support objects
        raise Exception("Unsupported inferred_type {0}".format(inferred_type))

        converted = np.asarray(values, dtype='O')
        return converted, inferred_type, tb.ObjectAtom()
    elif inferred_type == 'datetime':
        converted = np.array([(time.mktime(v.timetuple()) +
                            v.microsecond / 1E6) for v in values],
                            dtype=np.float64)
        return converted, inferred_type, tb.Time64Atom()
    elif inferred_type == 'integer':
        converted = np.asarray(values, dtype=np.int64)
        return converted, inferred_type, tb.Int64Atom()
    elif inferred_type == 'floating':
        converted = np.asarray(values, dtype=np.float64)
        return converted, inferred_type, tb.Float64Atom()
    raise Exception("Unsupported inferred_type {0} {1}".format(inferred_type, str(values[-5:])))

def _handle(obj):
    if isinstance(obj, tb.file.File):
        handle = obj
    else:
        handle = obj._v_file

    return _wrap(handle)

    
def _meta(obj, meta=None):
    obj = _unwrap(obj)

    if isinstance(obj, tb.file.File):
        obj = obj.root
        return _meta_file(obj, meta)

    handle = _handle(obj)
    type = handle.type
    if type == 'directory':
        return _meta_dir(obj, meta)

    return _meta_file(obj, meta)

def _meta_file(obj, meta):
    if meta:
        obj._v_attrs.pd_meta = meta
        return

    try:
        meta = obj._v_attrs.pd_meta
        if isinstance(meta, str):
            meta = pickle.loads(meta)
        return meta
    except:
        return {}

def _meta_path(obj):
    import os.path

    dir = os.path.dirname(obj._v_file.filename)
    filename = obj._v_pathname[1:]
    bits = filename.split('/')
    bits.append('meta')
    filename = ".".join(bits)
    filepath = os.path.join(dir, filename)
    return filepath


def _meta_dir(obj, meta=None):
    filepath = _meta_path(obj)
    if meta:
        with open(filepath, 'wb') as f:
            pickle.dump(meta, f)
        return

    try:
        with open(filepath, 'rb') as f:
            meta = pickle.load(f)
        return meta
    except:
        return {}

def _name(table):
    try:
        name = table.attrs.pandas_name
    except:
        name = table._v_name
    return name

def _columns(table):
    try:
        columns = list(_meta(table)['columns'])
    except:
        # assume first is index
        columns = table.colnames[1:]
    return columns

def _index_name(obj):
    if isinstance(obj, pd.DataFrame):
        return _index_name_frame(obj)
    return _index_name_table(obj)

def _index_name_table(table):
    try:
        index_name = _meta(table)['index_name']
    except:
        # assume first is index
        index_name = table.colnames[0]
    return index_name

def _index_name_frame(df):
    #TODO support multiindex
    index = df.index


def unconvert_obj(values, type):
    if type == 'datetime64':
        return values.astype("M8[ns]")
    if type == 'string':
        return values.astype(np.unicode_)

    return values

def unconvert_index(index_values, type):
    return pdtables._unconvert_index(index_values, type)

def create_table(group, name, desc, types, filters=None, expectedrows=None, title=None, columns=None, index_name=None, extra_meta=None):
    if title is None:
        title = name

    with warnings.catch_warnings(): # ignore the name warnings
        table = group._v_file.createTable(group, name, desc, title,
                                  expectedrows=expectedrows, filters=filters)

    meta = {}
    meta['columns'] = columns or list(desc.keys())
    meta['value_types'] = types
    meta['index_name'] = index_name
    meta['name'] = name
    if extra_meta:
        meta.update(extra_meta)

    _meta(table, meta)

    return table

def frame_to_table(name, df, group, filters=None, expectedrows=None, create_only=False, *args, **kwargs):
    """
        create_only will create the table but not appending the DF.
        Since the machinery for figuring out a table definition and converting values for
        appending are the same.
    """
    # TODO: potentially could change this to subset the DF so we don't convert and iterate over all
    # the values
    hfile = group._v_file

    # kind of a kludge to get series to work
    if isinstance(df, pd.Series):
        series_name = 'vals'
        df = pd.DataFrame({series_name:df}, index=df.index)

    desc, recs, types = convert_frame(df)
    columns = list(df.columns)
    index_name = df.index.name or 'pd_index'
    table = create_table(group, name, desc, types, filters=filters, columns=columns,
                         expectedrows=expectedrows, index_name=index_name,*args, **kwargs)
    if not create_only:
        table.append(recs)

    hfile.flush()

def table_to_frame(table, where=None):
    """
        Simple converison of table to DataFrame
    """
    if where:
        try:
            data = table_where(table, where)
        except Exception as err:
            raise Exception("readWhere error: {0} {1}".format(where, str(err)))
    else:
        data = table.read()


    df = table_data_to_frame(data, table)
    return df

def copy_table_def(group, name, orig):
    table_meta = _meta(orig)
    desc = orig.description
    types = table_meta['value_types']
    index_name = table_meta['index_name']
    columns = table_meta['columns']
    expectedrows = orig.nrows
    table = group.create_table(name, desc, types, columns=columns, index_name=index_name, expectedrows=expectedrows)
    return table


def table_where(table, where):
    """
        Optimized Where
    """
    return table.readWhere(where)

def get_table_index(table, index_name=None, types=None):
    """
        Get the pandas index from a pytable
    """
    if index_name is None:
        index_name = _index_name(table)

    if index_name is None: #neither passed in or set in meta
        return None

    if types is None:
        meta = _meta(table)
        types = meta.setdefault('value_types', {})

    index_values = table.col(index_name)
    index = unconvert_index(index_values, types[index_name])
    return index

def _data_names(data):
    if hasattr(data, 'keys'):
        return list(data.keys())

    if hasattr(data, 'dtype'):
        return data.dtype.names

def table_data_to_frame(data, table, columns=None):
    """
        Given the pytables.recarray data and the metadata taken from table, 
        create a DataFrame
    """
    columns = columns or _columns(table)
    index_name = _index_name(table)
    name = _name(table)

    meta = _meta(table)
    types = meta.setdefault('value_types', {})

    index = None
    if index_name:
        if index_name not in _data_names(data): # handle case where we dont send index with data
            index_values = table.col(index_name)
        else:
            index_values = data[index_name]
        index = unconvert_index(index_values, types[index_name])

    try:
        columns.remove(index_name)
    except ValueError:
        pass

    sdict = {}
    for col in columns:
        # recarrays have only str columns
        temp = data[str(col)]
        temp = unconvert_obj(temp, types[col])
        sdict[col] = temp

    df = pd.DataFrame(sdict, columns=columns, index=index)
    df.name = name
    return df

def _convert_param(param, base_type=None):
    """
        A well not thought out function to convert params to the proper base type. 
    """
    if base_type == 'datetime64' and isinstance(param, str):
        return pd.Timestamp(param).value

    if isinstance(param, str): # quote the string params
        param = "{0}".format(param.encode('UTF8'))

    if isinstance(param, pd.Timestamp): # Timestamp itself is never valid type
        param = param.value

    return param

class HDFSql(object):
    """
        HDFSql object. Kept in separate obj so we don't polute __getattr__ on table
    """
    def __init__(self, table, mapping=None):
        # TODO I could coalesce all types/mapping/table into one dict 
        # so HDFSql doesn't need to know about the table
        self.table = table
        self.mapping = mapping or {}
        # assuming meta won't change during object lifetime...
        self.meta = _meta(table)
        self.types = self.meta['value_types']

    def __getattr__(self, key):
        key = self.get_valid_key(key)
        try: 
            type = self.types[key]
        except:
            type = None

        return HDFQuery(key, type)
        raise AttributeError("No column")

    def get_valid_key(self, key):
        if key in self.table.colnames:
            return key
        # shortcuts
        if key == 'index':
            return _index_name(self.table)
        if key in self.mapping:
            return self.mapping[key]
        raise AttributeError("No column")

class HDFQuery(object):

    def __init__(self, base, base_type=None):
        self.base = base
        self.base_type = base_type

    def base_op(self, other, op):
        """ quick convert to pytable expression """
        base = "{0} {1} {2}".format(self.base, op, _convert_param(other, self.base_type))
        return HDFQuery(base, 'statement')

    __eq__  = lambda self, other: self.base_op(other, "==")
    __gt__  = lambda self, other: self.base_op(other, ">")
    __ge__  = lambda self, other: self.base_op(other, ">=")
    __lt__  = lambda self, other: self.base_op(other, "<")
    __le__  = lambda self, other: self.base_op(other, "<=")

    def __and__(self, other):
        base = "({0}) & ({1})".format(self.base, other)
        return HDFQuery(base)

    def __or__(self, other):
        base = "({0}) | ({1})".format(self.base, other)
        return HDFQuery(base)

    def __repr__(self):
        return str(self.base)

def hdf5_obj_repr(self, obj):
    cls = self.__class__.__name__
    return "{0}\n\n{1}".format(cls, repr(obj))

class HDF5Wrapper(object):
    def __repr__(self):
        return hdf5_obj_repr(self, self.obj)

    def keys(self):
        return list(self.obj._v_children.keys())

    def meta(self, key=None, value=None):
        meta = _meta(self)
        if key and value:
            meta[key] = value
            # store meta
            _meta(self, meta)
            return meta
        if key:
            # single val
            return meta[key]
        return meta


def _unwrap(obj):
    if isinstance(obj, HDF5Wrapper):
        return obj.obj
    return obj

def _wrap(obj, parent=None):
    """
        Wrap the pytables object with an appropiate Object. 
        Note: since only obj, parent is passed in here, all other params need to be stored
        in _meta. This is to make creation/reading the same process
    """
    if isinstance(obj, tb.group.RootGroup):
        return HDF5Group(obj, parent)
    if isinstance(obj, tb.Group):
        return HDF5Group(obj, parent)
    if isinstance(obj, tb.Table):
        return HDF5Table(obj)
    if isinstance(obj, tb.file.File):
        return HDF5Handle(obj)
    return obj

class HDF5Handle(HDF5Wrapper):
    """
        This wraps around the handle object
    """
    def __init__(self, filepath, mode='a', type=None):
        if isinstance(filepath, tb.file.File):
            return self._init_from_handle(filepath)

        self.filepath = filepath
        self.mode = mode
        self.obj = None
        self.obj = self.open(self.mode)

        meta = _meta(self.obj)
        if 'type' in meta:
            assert type is None or meta['type'] == type # these should never mismatch
            type = meta['type']

        if type is None:
            type = 'file' # default

        if self.mode != 'r':
            meta['type'] = type
            _meta(self.obj, meta)


    def _init_from_handle(self, handle):
        self.filepath = handle.filename
        self.mode = handle.mode
        self.obj = handle
        meta = _meta(handle)
        type = meta.setdefault('type', 'file')
        if self.mode != 'r':
            _meta(handle, meta)
        self.type = type

    @property
    def handle(self):
        return self.obj

    def keys(self):
        return list(self.root._v_children.keys())

    def reopen(self):
        self.obj = self.open(self.mode)

    def open(self, mode="a", warn=True):
        handle = tb.openFile(self.filepath, mode)
        return handle

    def close(self):
        if self.obj is not None and self.obj.isopen:
            self.obj.close()

    def create_group(self, group_name, filters=None, meta=None, root=None):
        """
            Create HDFPanelGroup
        """
        handle = self.handle    
        if root is None:
            root = handle.root
        group = handle.createGroup(root, group_name, group_name, filters=filters)

        if meta is None:
            meta = {}
            meta['group_type'] = 'default'

        meta['filters'] = filters

        _meta(group, meta)

        return _wrap(group, self)

    def __getattr__(self, key):
        if hasattr(self.obj, key):
            val = getattr(self.obj, key)
            return _wrap(val, self)
        if hasattr(self.obj.root, key):
            val = getattr(self.obj.root, key)
            return _wrap(val, self)
        raise AttributeError()

    def __getitem__(self, key):
        if hasattr(self.obj.root, key):
            val = getattr(self.obj.root, key)
            return _wrap(val, self)
        raise KeyError()

class HDF5Group(HDF5Wrapper):
    def __init__(self, group, handle):
        self.obj = group
        self.handle = handle
        self.filters = None

    @property
    def group(self):
        return self.obj

    def create_table(self, name, desc, types, filters=None, expectedrows=None, title=None, columns=None, index_name=None):
        table = create_table(self.group, name, desc, types, 
                             filters, expectedrows, title, columns, index_name)
  
        return _wrap(table)

    def frame_to_table(self, name, df, *args, **kwargs):
        group = self.group
        frame_to_table(name, df, group, *args, **kwargs)

    def create_group(self, *args, **kwargs):
        return self.handle.create_group(*args, root=self.obj, **kwargs)

    def __getitem__(self, key):
        if hasattr(self.obj, key):
            val = getattr(self.obj, key)
            return _wrap(val)
        raise KeyError()

    def __getattr__(self, key):
        if hasattr(self.obj, key):
            val = getattr(self.obj, key)
            return _wrap(val)
        raise AttributeError()


class HDF5Table(HDF5Wrapper):
    def __init__(self, table, mapping=None, cache_index=True):
        self.obj = table
        self.mapping = mapping or {}
        self.cache_index = cache_index
        self._index = None
        self._ix = None

    _columns = None
    @property
    def columns(self):
        if self._columns is None:
            self._columns = _meta(self.table)['columns']
        return self._columns

    @property
    def table(self):
        return self.obj

    @property
    def index(self):
        if self._index is None and self.cache_index:
            self._index = CachingIndex(self)

        return self._index

    def append(self, data, flush=False):
        if isinstance(data, pd.DataFrame):
            self._append_frame(data, flush)

    def _append_frame(self, df, flush=False):
        desc, recs, types = convert_frame(df)

        if not np.all(df.columns == self.columns):
            raise MismatchColumnsError("HDFTable and DataFrame columns are not the same {0} vs {1}".format(
                df.columns, self.columns))
        self.table.append(recs)
        if flush:
            self.table.flush()

    def keys(self):
        return self.table.colnames

    @property
    def sql(self):
        return HDFSql(self.table, self.mapping)

    def __getitem__(self, key):
        # TODO This can be faster if we cache the getWhereList somewhere on disk
        key = _convert_param(key)
        if isinstance(key, HDFQuery):
            return self.query(key)

        if isinstance(key, slice):
            data = self.table[key]
            df = table_data_to_frame(data, self.table)
            return df

        if isinstance(key, np.ndarray):
            if key.dtype == 'bool':
                return self._getitem_bools(key)
            if key.dtype == 'int':
                return self._getitem_ints(key)

        try:
            # list of slices
            if isinstance(key[0], slice):
                return self._getitem_slices(key)
        except:
            pass

    def _getitem_slices(self, key):
        parts = []
        for slice in key:
            part = self.table[slice]
            parts.append(part)

        data = np.concatenate(parts)
        df = table_data_to_frame(data, self.table)
        return df

    def _getitem_ints(self, key):
        slices = create_slices(key)
        return self._getitem_slices(slices)

    def _getitem_bools(self, key):
        slices = create_slices(key)
        return self._getitem_slices(slices)

    def query(self, query):
        where = str(query)
        df = table_to_frame(self.table, where=where)
        return df

    def __getattr__(self, key):
        if hasattr(self.obj, key):
            val = getattr(self.obj, key)
            return _wrap(val)
        raise AttributeError()

    @property
    def ix(self):
        # start splitting out
        if self._ix is None:
            self._ix = SimpleIndexer(self)
        return self._ix     

    def add_index(self, col):
        column = self.col(col)
        if not column.is_indexed:
            print(("Creating Index on {0}".format(col)))
            num = column.createCSIndex()
            print(("Index created with {0} vals".format(num)))
        else:
            print(("Index already exists {0}. Reindex?".format(col)))

    def reindex(self, col):
        column = self.col(col)
        if column.is_indexed:
            print(("Re-indexing on {0}".format(col)))
            column.reIndex()
        else:
            print(("{0} is not indexed".format(col)))

    def reindex_all(self):
        cols = self.table.colnames
        for col in cols:
            self.reindex(col)

class CachingIndex(object):
    def __init__(self, obj):
        self.obj = obj
        self._index = get_table_index(obj.table)

    def __getattr__(self, key):
        if hasattr(self._index, key):
            return getattr(self._index, key)
        raise AttributeError()

    __eq__ = lambda self, other: self._comparison('__eq__', other)
    __ne__ = lambda self, other: self._comparison('__ne__', other)
    __gt__ = lambda self, other: self._comparison('__gt__', other)
    __ge__ = lambda self, other: self._comparison('__ge__', other)
    __lt__ = lambda self, other: self._comparison('__lt__', other)
    __le__ = lambda self, other: self._comparison('__le__', other)

    def _comparison(self, op, other):
        # TODO add gt, ge, lt, le comparisons that output IndexSlice.
        index_op = getattr(self._index, op)
        if isinstance(self._index, pd.DatetimeIndex):
            return self._datetime_comparison(index_op, other)
        result = index_op(other)
        return result

    def _datetime_comparison(self, op, other):
        other = pd.Timestamp(other)
        return op(other)

    def __repr__(self):
        return repr(self._index)

    def refresh(self):
        self._index = get_table_index(self.obj.table)

    def between(self, start, end):
        """
            Between dates, inclusive
        """
        if isinstance(self._index, pd.DatetimeIndex):
            start = pd.Timestamp(start)
            end = pd.Timestamp(end)
        first = self.searchsorted(start)
        last = self.searchsorted(end, side="right")
        return IndexSlice(first, last)

class SimpleIndexer(object):
    def __init__(self, obj):
        self.obj = obj

    def __getitem__(self, key):
        # TODO, get fancier slicing later on
        if isinstance(key, tuple):
            return self._getitem_tuple(key)
        if isinstance(key, IndexSlice):
            key = slice(key.start, key.end, key.step)
        return self.obj[key]

    def _getitem_tuple(self, key):
        # TODO check if this is faster than just grabbing the whole
        rows = key[0]
        if isinstance(rows, IndexSlice):
            rows = slice(rows.start, rows.end, rows.step)

        cols = key[1]
        if isinstance(cols, str):
            cols = [cols]

        # grabbing the straight data. obj is an HDF5Table. obj.obj is table.Table
        if len(cols) > 1:
            data = self.obj.obj[rows]
        else:
            # this doesn't seem to be all that much faster, keeping in anyways
            data = {}
            col = cols[0]
            data[col] = self.obj.obj.col(col)

        return table_data_to_frame(data, self.obj, columns=cols)

class IndexSlice(object):
    def __init__(self, start=None, end=None, step=None):
        self.start = start
        self.end = end
        self.step = step

    def __and__(self, other):
        if self.start is None:
            self.start = other.start
        if self.end is None:
            self.end = other.end

# IPYTYHON
def install_ipython_completers():  # pragma: no cover
    """Register the DataFrame type with IPython's tab completion machinery, so
    that it knows about accessing column names as attributes."""
    from IPython.utils.generics import complete_object
    from pandas import compat

    @complete_object.when_type(CachingIndex)
    def complete_index(obj, prev_completions):
        return prev_completions + [c for c in dir(obj._index) \
                    if isinstance(c, str) and compat.isidentifier(c)]                                          
# Importing IPython brings in about 200 modules, so we want to avoid it unless
# we're in IPython (when those modules are loaded anyway).
import sys
if "IPython" in sys.modules:  # pragma: no cover
    try: 
        install_ipython_completers()
    except Exception:
        print('exception')
        pass 
