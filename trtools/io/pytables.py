import warnings
from collections import OrderedDict
from itertools import izip

from tables import *
import pandas as pd
import pandas.lib as lib
import numpy as np

from trtools.io.common import _filename

MIN_ITEMSIZE = 10

def convert_frame(df):
    """
        Input: DataFrame
        Output: pytable table description and pytable compatible recarray
    """
    sdict = OrderedDict()
    atoms = OrderedDict()

    #index
    index_name = df.index.name or 'pd_index'
    converted, atom = _convert_obj(df.index)
    atoms[index_name] = atom
    sdict[index_name] = converted

    # columns
    for col in df.columns:
        converted, atom = _convert_obj(df[col])
        atoms[col] = atom
        sdict[col] = converted

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
    return desc, recs

def _convert_obj(obj):
    if isinstance(obj, pd.DatetimeIndex):
        converted = obj.asi8
        return converted, Int64Atom()
    elif isinstance(obj, (pd.Int64Index, pd.PeriodIndex)):
        converted = obj.values
        return converted, Int64Atom()

    inferred_type = lib.infer_dtype(obj)
    values = np.asarray(obj)

    if inferred_type == 'datetime64':
        converted = values.view('i8')
        return converted, Int64Atom()
    if inferred_type == 'string':
        converted = np.array(list(values), dtype=np.str_)
        itemsize = converted.dtype.itemsize
        # for OBT, can't assume value will be right for future
        # frame keys
        if itemsize < MIN_ITEMSIZE:
            itemsize = MIN_ITEMSIZE
            converted = converted.astype("S{0}".format(itemsize))
        return converted, StringAtom(itemsize)
    elif inferred_type == 'unicode':
        # table's don't seem to support objects
        raise Exception("Unsupported inferred_type {0}".format(inferred_type))

        converted = np.asarray(values, dtype='O')
        return converted, ObjectAtom()
    elif inferred_type == 'datetime':
        return Time64Atom()
    elif inferred_type == 'integer':
        converted = np.asarray(values, dtype=np.int64)
        return converted, Int64Atom()
    elif inferred_type == 'floating':
        converted = np.asarray(values, dtype=np.float64)
        return converted, Float64Atom()

    raise Exception("Unsupported inferred_type {0}".format(inferred_type))
    

def _get_atom(obj, check_string=False):
    if isinstance(obj, pd.DatetimeIndex):
        return Int64Atom()
    elif isinstance(obj, (pd.Int64Index, pd.PeriodIndex)):
        return Int64Atom()

    inferred_type = lib.infer_dtype(obj)

    if inferred_type == 'datetime64':
        return Int64Atom()
    if inferred_type == 'string':
        # unless we're indexing, we don't care about string?
        if not check_string:
            return ObjectAtom()
        converted = np.array(list(obj.values), dtype=np.str_)
        itemsize = converted.dtype.itemsize
        # for OBT, can't assume value will be right for future
        # frame keys
        itemsize = max(itemsize, MIN_ITEMSIZE)
        return StringAtom(itemsize)
    elif inferred_type == 'unicode':
        return ObjectAtom()
    elif inferred_type == 'datetime':
        return Time64Atom()
    elif inferred_type == 'integer':
        return Int64Atom()
    elif inferred_type == 'floating':
        return Float64Atom()
    
    return ObjectAtom()

def _meta(obj):
    try:
        return obj._v_attrs.pd_meta
    except:
        return {}

def get_col(obj, pos=None):
    """
        Get the tables.Col from dtype
    """
    atom = _get_atom(obj)
    return Col.from_atom(atom, pos=pos) 

def _name(table):
    try:
        name = table.attrs.pandas_name
    except:
        name = table._v_name
    return name

def _columns(table):
    try:
        columns = table.attrs.pandas_columns
    except:
        # assume first is index
        columns = table.colnames[1:]
    return columns

def _index_name(table):
    try:
        index_name = table.attrs.pandas_index_name
    except:
        # assume first is index
        index_name = table.colnames[0]
    return index_name

def _index_type(table):
    try:
        index_type = table.attrs.pandas_index_type
    except:
        iname = _index_name(table)
        index_type = getattr(table.cols, iname).dtype
        if index_type.type == np.int64 and 'time' in iname:
            index_type = np.dtype('M8[ns]')

    return index_type

def frame_description(df):
    """
        Generate the tables.Table description from DataFrame
        Keeps track of positions, though we store df.columns
        as well
    """
    desc = {}
    pos = 0

    #index
    index_name = df.index.name or 'pd_index'
    desc[index_name] = get_col(df.index, pos)
    pos += 1

    # columns
    for col in df.columns:
        desc[col] = get_col(df[col], pos)
        pos += 1
    return desc

def convert_index(index):
    if isinstance(index, pd.DatetimeIndex):
        return index.asi8

def unconvert_index(index_values, index_dtype):
    if index_dtype.type == np.datetime64:
        return pd.DatetimeIndex(index_values)

def create_table_from_frame(name, df, hfile, hgroup, desc):
    with warnings.catch_warnings(): # ignore the name warnings
        warnings.simplefilter("ignore")
        table = hfile.createTable(hgroup, _filename(name), desc, str(name),
                                  expectedrows=len(df))

    table.attrs.pandas_columns = df.columns
    table.attrs.pandas_index_name = df.index.name or 'pd_index'
    table.attrs.pandas_index_type = df.index.dtype
    table.attrs.pandas_name = name
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

    desc, recs = convert_frame(df)
    table = create_table_from_frame(name, df, hfile, hgroup, desc)

    # TODO this is fast but can't support multiindex
    table.append(recs)

    hfile.flush()

def table_to_frame(table, where=None):
    """
        Convert pytable table to dataframe
    """
    columns = _columns(table)
    index_name = _index_name(table)
    index_type = _index_type(table)
    name = _name(table)


    if where:
        data = table.readWhere(where)
    else:
        data = table.read()

    df = table_data_to_frame(data, columns, index_name, index_type)

    df.name = name
    return df

def table_data_to_frame(data, columns, index_name, index_type):
    index_values = data[index_name]
    index = unconvert_index(index_values, index_type)

    sdict = {}
    for col in columns:
        sdict[col] = data[col]

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

    def open(self, mode="a", warn=True):
        if self.handle is not None and self.handle.isopen:
            self.handle.close()
        return openFile(self.filepath, mode)

    def groups(self):
        handle = self.handle
        nodes = handle.root._f_listNodes()
        return [node._v_name for node in nodes]

    def get_group(self, group):
        handle = self.handle
        group = handle.root._f_getChild(group)

        meta = _meta(group)
        group_type = meta.setdefault('group_type', 'panel')
        klass = HDFPanelGroup
        if group_type == 'obt':
            print meta
            klass = OBTGroup
        return klass(group, self, **meta)

    def create_group(self, group_name):
        handle = self.handle    
        group = handle.createGroup(handle.root, group_name, group_name)

        meta = {}
        meta['group_type'] = 'panel'

        group._v_attrs.pd_meta = meta

        return HDFPanelGroup(group, self)

    def create_obt(self, group_name, frame_key=None, table_name=None):
        handle = self.handle    
        group = handle.createGroup(handle.root, group_name, group_name)

        frame_key = frame_key or 'frame_key'
        table_name = table_name or group._v_name

        meta = {}
        meta['frame_key'] = frame_key
        meta['table_name'] = table_name
        meta['group_type'] = 'obt'

        group._v_attrs.pd_meta = meta

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

    def get_data(self, name, start=None, end=None):
        table = self.get_table(name)
        df = self._get_data(table, start, end)
        return df

    def get_all(self, start=None, end=None):
        ret = {}
        for node in self.group._f_iterNodes():
            df = self._get_data(node, start, end)
            ret[node._v_name] = df
        return ret
            
    def _get_data(self, table, start=None, end=None):
        index_name = _index_name(table)
        where = []
        if start:
            start = pd.Timestamp(start).value
            start_where = "({0} > {1})".format(index_name, start)
            where.append(start_where)
        if end:
            end = pd.Timestamp(end).value
            end_where = "({0} < {1})".format(index_name, end)
            where.append(end_where)

        if len(where) > 0:
            where = " & ".join(where)
        else:
            where = None

        df = table_to_frame(table, where=where)
        return df

    def keys(self):
        return self.group._v_children.keys()

    def create_table(self, df, name=None):
        handle = self.panel.handle
        table = frame_to_table(df, handle, self.group, name=name)
        return table

    def append(self, df, name=None):
        table = self.get_table(name)
        desc, recs = convert_frame(df)
        table.append(recs)

    def __setitem__(self, key, value):
        self.create_table(value, name=key)

    def __getitem__(self, key):
        return self.get_data(key)

    def add_index(self):
        #TODO add indexes to all
        pass

    def foreach(self, func):
        pass
        # call func on each node

class OBTGroup(HDFPanelGroup):
    def __init__(self, group, panel, frame_key, table_name, *args, **kwargs):
        super(OBTGroup, self).__init__(group, panel, *args, **kwargs)

        self.frame_key = frame_key
        self.table_name = table_name
        self._table = None

    def __setitem__(self, key, value):
        value[self.frame_key] = key
        table_name = self.table_name
        if hasattr(self.group, table_name):
            self.append(value, name=table_name)
        else:
            table = self.create_table(value, name=table_name)
            self._table = table

    def __getitem__(self, key):
        if isinstance(key, basestring):
            key = "'{0}'".format(key)
        where = "{0} == {1}".format(self.frame_key, key)
        df = table_to_frame(self.table, where=where)
        del df[self.frame_key]
        return df

    def get_all(self, start=None, end=None):
        # not sure if this should be a dict of DFs
        all_df = table_to_frame(self.table)
        return all_df

    @property
    def table(self):
        if self._table is None:
            self._table = self.get_table(self.table_name)

        return self._table

    def keys(self):
        data = self.table.col(self.frame_key)
        return list(np.unique(data))

