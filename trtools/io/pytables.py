import warnings
from itertools import izip

from tables import *
import pandas as pd
import numpy as np

from trtools.io.common import _filename

def get_atom(dtype):
    try:
        return Atom.from_dtype(dtype)
    except:
        pass

    if dtype.type == np.datetime64:
        return Int64Atom()

def get_col(dtype, pos=None):
    """
        Get the tables.Col from dtype
    """
    atom = get_atom(dtype)
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
    desc[index_name] = get_col(df.index.dtype, pos)
    pos += 1

    # columns
    for col in df.columns:
        desc[col] = get_col(df[col].dtype, pos)
        pos += 1
    return desc

def convert_index(index):
    if isinstance(index, pd.DatetimeIndex):
        return index.asi8

def unconvert_index(index_values, index_dtype):
    if index_dtype.type == np.datetime64:
        return pd.DatetimeIndex(index_values)

def frame_to_table(df, hfile, hgroup, name=None):

    if name is None:
        name = df.name

    # kind of a kludge to get series to work
    if isinstance(df, pd.Series):
        series_name = 'vals'
        df = pd.DataFrame({series_name:df}, index=df.index)

    desc = frame_description(df)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        table = hfile.createTable(hgroup, _filename(name), desc, str(name),
                                  expectedrows=len(df))

    table.attrs.pandas_columns = df.columns
    table.attrs.pandas_index_name = df.index.name or 'pd_index'
    table.attrs.pandas_index_type = df.index.dtype
    table.attrs.pandas_name = name

    # TODO this is fast but can't support multiindex
    table.append(df.to_records())

    hfile.flush()

def table_to_frame(table, where=None):
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
    def __init__(self, filepath):
        self.filepath = filepath
        self.handle = self.get_handle()

    def get_handle(self):
        return openFile(self.filepath)

    def groups(self):
        handle = self.handle
        nodes = handle.root._f_listNodes()
        return [node._v_name for node in nodes]

    def get_group(self, group):
        handle = self.handle
        group = handle.root._f_getChild(group)
        return HDFPanelGroup(group)

class HDFPanelGroup(object):
    def __init__(self, group):
        self.group = group

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
            #df = self._get_data(node, start, end)
            df = node.read()
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

    def add_index(self):
        #TODO add indexes to all
        pass

    def foreach(self, func):
        pass
        # call func on each node

