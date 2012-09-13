import warnings
from collections import OrderedDict
from itertools import izip
import cPickle as pickle

from tables import *
import pandas as pd
import pandas.lib as lib
import numpy as np
import pandas.io.pytables as pdtables

from trtools.io.common import _filename

MIN_ITEMSIZE = 10

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
        col = Col.from_atom(atom, pos=pos) 
        desc[str(k)] = col

    # create recarray
    dtypes = [(str(k), v.dtype) for k, v in sdict.items()]
    recs = np.recarray(shape=len(df), dtype=dtypes)
    for k, v in sdict.items():
        recs[str(k)] = v
    return desc, recs, types

def _convert_obj(obj):
    """
        Convert a series to pytables values and Atom
    """
    if isinstance(obj, pd.DatetimeIndex):
        converted = obj.asi8
        return converted, 'datetime64', Int64Atom()
    elif isinstance(obj, pd.PeriodIndex):
        converted = obj.values
        return converted, 'periodindex', Int64Atom()
    elif isinstance(obj, pd.PeriodIndex):
        converted = obj.values
        return converted, 'int64', Int64Atom()

    inferred_type = lib.infer_dtype(obj)
    values = np.asarray(obj)

    if inferred_type == 'datetime64':
        converted = values.view('i8')
        return converted, inferred_type, Int64Atom()
    if inferred_type == 'string':
        converted = np.array(list(values), dtype=np.str_)
        itemsize = converted.dtype.itemsize
        # for OBT, can't assume value will be right for future
        # frame keys
        if itemsize < MIN_ITEMSIZE:
            itemsize = MIN_ITEMSIZE
            converted = converted.astype("S{0}".format(itemsize))
        return converted, inferred_type, StringAtom(itemsize)
    elif inferred_type == 'unicode':
        # table's don't seem to support objects
        raise Exception("Unsupported inferred_type {0}".format(inferred_type))

        converted = np.asarray(values, dtype='O')
        return converted, inferred_type, ObjectAtom()
    elif inferred_type == 'datetime':
        converted = np.array([(time.mktime(v.timetuple()) +
                            v.microsecond / 1E6) for v in values],
                            dtype=np.float64)
        return converted, inferred_type, Time64Atom()
    elif inferred_type == 'integer':
        converted = np.asarray(values, dtype=np.int64)
        return converted, inferred_type, Int64Atom()
    elif inferred_type == 'floating':
        converted = np.asarray(values, dtype=np.float64)
        return converted, inferred_type, Float64Atom()
    raise Exception("Unsupported inferred_type {0} {1}".format(inferred_type, str(values[-5:])))
    
def _meta(obj, meta=None):
    if meta:
        obj._v_attrs.pd_meta = meta
        return

    try:
        meta = obj._v_attrs.pd_meta
        if isinstance(meta, basestring):
            meta = pickle.loads(meta)
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

def _index_name(table):
    try:
        index_name = _meta(table)['index_name']
    except:
        # assume first is index
        index_name = table.colnames[0]
    return index_name

def unconvert_obj(values, type):
    if type == 'datetime64':
        return values.astype("M8[ns]")

    return values

def unconvert_index(index_values, type):
    return pdtables._unconvert_index(index_values, type)

def create_table_from_frame(name, df, hfile, hgroup, desc, types, filters=None, 
                            expectedrows=None):
    if expectedrows is None:
        expectedrows = len(df)
    with warnings.catch_warnings(): # ignore the name warnings
        warnings.simplefilter("ignore")
        print 'Expected rows{0}'.format(expectedrows)
        table = hfile.createTable(hgroup, _filename(name), desc, str(name),
                                  expectedrows=expectedrows, filters=filters)

    meta = {}
    meta['columns'] = list(df.columns)
    meta['value_types'] = types
    meta['index_name'] = df.index.name or 'pd_index'
    meta['name'] = name

    _meta(table, meta)

    return table

def frame_to_table(df, hfile, hgroup, name=None, filters=None, *args, **kwargs):
    """
    """
    if name is None:
        name = df.name

    # kind of a kludge to get series to work
    if isinstance(df, pd.Series):
        series_name = 'vals'
        df = pd.DataFrame({series_name:df}, index=df.index)

    desc, recs, types = convert_frame(df)
    table = create_table_from_frame(name, df, hfile, hgroup, desc, types, filters=filters, 
                                   *args, **kwargs)
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

def table_where(table, where):
    """
        Optimized Where
    """
    return table.readWhere(where)

def table_data_to_frame(data, table):
    """
        Given the pytables.recarray data and the metadata taken from table, 
        create a DataFrame
    """
    columns = _columns(table)
    index_name = _index_name(table)
    name = _name(table)

    meta = _meta(table)
    types = meta.setdefault('value_types', {})

    index = None
    if index_name:
        index_values = data[index_name]
        index = unconvert_index(index_values, types[index_name])

    try:
        del columns['index_name']
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
    if base_type == 'datetime64' and isinstance(param, basestring):
        return pd.Timestamp(param).value

    if isinstance(param, basestring): # quote the string params
        param = "'{0}'".format(param)

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
        return self.obj._v_children.keys()

def _wrap(obj, parent=None):
    """
        Wrap the pytables object with an appropiate Object. 
        Note: since only obj, parent is passed in here, all other params need to be stored
        in _meta. This is to make creation/reading the same process
    """
    if isinstance(obj, Group):
        return HDF5Group(obj, parent)
    if isinstance(obj, Table):
        return HDF5Table(obj)
    return obj

class HDF5Handle(HDF5Wrapper):
    """
        This wraps around the handle object
    """
    def __init__(self, filepath, mode='a'):
        self.filepath = filepath
        self.mode = mode
        self.obj = None
        self.obj = self.open(self.mode)

    @property
    def handle(self):
        return self.obj

    @property
    def root(self):
        return self.handle.root

    def reopen(self):
        self.obj = self.open(self.mode)

    def open(self, mode="a", warn=True):
        self.close()
        return openFile(self.filepath, mode)

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

        meta['filters'] = 'filters'

        _meta(group, meta)

        return _wrap(group, self)

    def __getattr__(self, key):
        if hasattr(self.obj, key):
            val = getattr(self.obj, key)
            return _wrap(val)
        raise AttributeError()

    def __getitem__(self, key):
        if hasattr(self.obj.root, key):
            val = getattr(self.obj.root, key)
            return _wrap(val)
        raise KeyError()

class HDF5Group(HDF5Wrapper):
    def __init__(self, group, handle):
        self.obj = group
        self.handle = handle
        self.filters = None

    @property
    def group(self):
        return self.obj

    def create_table(self, name, desc, types, filters=None, expectedrows=None, title=None, columns=None, index=None):
        if title is None:
            title = name

        with warnings.catch_warnings(): # ignore the name warnings
            table = self.handle.createTable(self.group, name, desc, title,
                                      expectedrows=expectedrows, filters=filters)

        meta = {}
        meta['columns'] = columns or desc.keys()
        meta['value_types'] = types
        meta['index_name'] = index
        meta['name'] = name

        _meta(table, meta)

        return _wrap(table)

    def __getitem__(self, key):
        if hasattr(self.obj, key):
            val = getattr(self.obj, key)
            return _wrap(val)
        raise KeyError()


class HDF5Table(HDF5Wrapper):
    def __init__(self, table, mapping=None):
        self.obj = table
        self.mapping = mapping or {}

    @property
    def table(self):
        return self.obj

    def append(self, data):
        if isinstance(data, pd.DataFrame):
            self._append_frame(data)

    def _append_frame(self, df, flush=False):
        desc, recs, types = convert_frame(df)
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

    def query(self, query):
        where = str(query)
        df = table_to_frame(self.table, where=where)
        return df

    def __getattr__(self, key):
        if hasattr(self.obj, key):
            val = getattr(self.obj, key)
            return _wrap(val)
        raise AttributeError()

