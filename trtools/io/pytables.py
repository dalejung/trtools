import warnings
from collections import OrderedDict
from itertools import izip

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
    desc = {}
    for pos, data in enumerate(atoms.items()):
        k, atom = data
        col = Col.from_atom(atom, pos=pos) 
        desc[k] = col

    # create recarray
    dtypes = [(k, v.dtype) for k, v in sdict.items()]
    recs = np.recarray(shape=len(df), dtype=dtypes)
    for k, v in sdict.items():
        recs[k] = v
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

    raise Exception("Unsupported inferred_type {0}".format(inferred_type))
    
def _meta(obj, meta=None):
    if meta:
        obj._v_attrs.pd_meta = meta
        return

    try:
        return obj._v_attrs.pd_meta
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
        columns = _meta(table)['columns']
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

def create_table_from_frame(name, df, hfile, hgroup, desc, types):
    with warnings.catch_warnings(): # ignore the name warnings
        warnings.simplefilter("ignore")
        table = hfile.createTable(hgroup, _filename(name), desc, str(name),
                                  expectedrows=len(df))

    meta = {}
    meta['columns'] = df.columns
    meta['value_types'] = types
    meta['index_name'] = df.index.name or 'pd_index'
    meta['name'] = name

    _meta(table, meta)

    return table

def frame_to_table(df, hfile, hgroup, name=None):
    """
    """
    if name is None:
        name = df.name

    # kind of a kludge to get series to work
    if isinstance(df, pd.Series):
        series_name = 'vals'
        df = pd.DataFrame({series_name:df}, index=df.index)

    desc, recs, types = convert_frame(df)
    table = create_table_from_frame(name, df, hfile, hgroup, desc, types)
    table.append(recs)
    hfile.flush()

def table_to_frame(table, where=None):
    """
        Convert pytable table to dataframe
    """
    columns = _columns(table)
    index_name = _index_name(table)
    name = _name(table)

    meta = _meta(table)
    types = meta.setdefault('value_types', {})

    if where:
        try:
            print "Where Clause: {0}\n".format(where)
            data = table.readWhere(where)
        except Exception as err:
            raise Exception("readWhere error: {0} {1}".format(where, str(err)))
    else:
        data = table.read()

    df = table_data_to_frame(data, columns, index_name, types)
    df.name = name
    return df

def table_data_to_frame(data, columns, index_name, types):
    index_values = data[index_name]
    index = unconvert_index(index_values, types[index_name])

    sdict = {}
    for col in columns:
        temp = data[col]
        temp = unconvert_obj(temp, types[col])
        sdict[col] = temp

    df = pd.DataFrame(sdict, columns=columns, index=index)
    return df

class HDFPanel(object):
    """
        Kind of like HDFStore but restricts it to a group of 
        similar DataFrames. Like panel except not sharing index
    """
    def __init__(self, filepath, mode='a'):
        self.handle = None
        self.filepath = filepath
        self.mode = mode
        self.handle = self.open(self.mode)

    def reopen(self):
        self.handle = self.open(self.mode)

    def open(self, mode="a", warn=True):
        self.close()
        return openFile(self.filepath, mode)

    def close(self):
        if self.handle is not None and self.handle.isopen:
            self.handle.close()

    def keys(self):
        return self.groups()

    def groups(self):
        handle = self.handle
        nodes = handle.root._f_listNodes()
        return [node._v_name for node in nodes]

    def get_group(self, group, *args, **kwargs):
        handle = self.handle
        group = handle.root._f_getChild(group)

        meta = _meta(group)
        old_meta = meta.copy()
        meta.update(kwargs)

        group_type = meta.setdefault('group_type', 'panel')

        # update meta if we're overidding here. probably better way to do this
        if old_meta != meta:
            _meta(group, meta)

        klass = HDFPanelGroup
        if group_type == 'obt':
            klass = OBTGroup
        return klass(group, self, **meta)

    def __getitem__(self, key):
        return self.get_group(key)

    def create_group(self, group_name):
        """
            Create HDFPanelGroup
        """
        handle = self.handle    
        group = handle.createGroup(handle.root, group_name, group_name)

        meta = {}
        meta['group_type'] = 'panel'

        _meta(group, meta)

        return HDFPanelGroup(group, self)

    def create_obt(self, group_name, frame_key=None, table_name=None):
        """
            Create OBTGroup
        """
        handle = self.handle    
        group = handle.createGroup(handle.root, group_name, group_name)

        frame_key = frame_key or 'frame_key'
        table_name = table_name or group._v_name

        meta = {}
        meta['frame_key'] = frame_key
        meta['table_name'] = table_name
        meta['group_type'] = 'obt'

        _meta(group, meta)

        return OBTGroup(group, self, **meta)

class HDFPanelGroup(object):
    pd_group_type = 'panel_group'

    def __init__(self, group, panel, *args, **kwargs):
        self.group = group
        self.panel = panel

    def get_table(self, name):
        group = self.group
        if hasattr(group, str(name)):
            return getattr(group, str(name))

        raise Exception("Name does not exist in this Group")

    def get_data(self, name):
        table = self.get_table(name)
        df = table_to_frame(table)
        return df

    def get_all(self, start=None, end=None):
        ret = {}
        for node in self.group._f_iterNodes():
            df = self._get_data(node, start, end)
            ret[node._v_name] = df
        return ret

    def keys(self):
        return self.group._v_children.keys()

    def create_table(self, df, name=None):
        handle = self.panel.handle
        table = frame_to_table(df, handle, self.group, name=name)
        return table

    def append(self, df, name=None):
        table = self.get_table(name)
        desc, recs, types = convert_frame(df)
        table.append(recs)

    def __setitem__(self, key, value):
        self.create_table(value, name=key)

    def __getitem__(self, key):
        return self.get_data(key)

    def foreach(self, func):
        pass
        # call func on each node

class OBTGroup(HDFPanelGroup):
    def __init__(self, group, panel, frame_key, table_name, copy=True, *args, **kwargs):
        super(OBTGroup, self).__init__(group, panel, *args, **kwargs)

        self.frame_key = frame_key
        self.table_name = table_name
        self._table = None
        self.copy = copy

    def __setitem__(self, key, value):
        # TODO This should be like mode 'w'. Where another method will be the append
        # Right now it will just append to the same frame_key
        ind = value.index
        if isinstance(value, pd.Series):
            value = {'vals': value}
        df = pd.DataFrame(value, index=ind, copy=self.copy) # not liking having to copy
        df[self.frame_key] = key # we copy cuz of this
        table_name = self.table_name
        if hasattr(self.group, table_name):
            self.append(df, name=table_name)
        else:
            table = self.create_table(df, name=table_name)
            self._table = table

    def __getitem__(self, key):
        # TODO This can be faster if we cache the getWhereList somewhere on disk

        key = _convert_param(key)
        if isinstance(key, HDFQuery):
            return self._getitem_query(key)
        if isinstance(key, slice):
            raise NotImplementedError('TODO work on slicing')
        return self._getitem_framekey(key)

    def _getitem_framekey(self, key):
        where = "{0} == {1}".format(self.frame_key, key)
        df = table_to_frame(self.table, where=where)
        del df[self.frame_key]
        return df

    def _getitem_query(self, query):
        where = str(query)
        df = table_to_frame(self.table, where=where)
        return df

    def get_all(self):
        all_df = table_to_frame(self.table)
        return all_df

    @property
    def table(self):
        if self._table is None:
            self._table = self.get_table(self.table_name)

        return self._table

    @property
    def sql(self):
        mappings = {'items' : self.frame_key}
        return HDFSql(self.table, mappings)

    def keys(self):
        data = self.table.col(self.frame_key)
        return list(np.unique(data))

    def __repr__(self):
        return repr(self.table)

    def col(self, col):
        column = getattr(self.table.cols, col)
        return column


    def add_index(self, col):
        column = self.col(col)
        if not column.is_indexed:
            print "Creating Index on {0}".format(col)
            num = column.createCSIndex()
            print "Index created with {0} vals".format(num)
        else:
            print "Index already exists {0}. Reindex?".format(col)

    def reindex(self, col):
        column = self.col(col)
        if column.is_indexed:
            print "Re-indexing on {0}".format(col)
            column.reIndex()
        else:
            print "{0} is not indexed".format(col)

    def reindex_all(self):
        cols = self.table.colnames
        for col in cols:
            self.reindex(col)

    def index_default(self):
        table_meta = _meta(self.table)
        index_name = table_meta['index_name']
        self.add_index(index_name)
        self.add_index(self.frame_key)


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
