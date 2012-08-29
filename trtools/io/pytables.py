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
    table = hfile.createTable(hgroup, _filename(name), desc, str(name),
                              expectedrows=len(df))

    table.attrs.pandas_columns = df.columns
    table.attrs.pandas_index_name = df.index.name or 'pd_index'
    table.attrs.pandas_index_type = df.index.dtype
    table.attrs.pandas_name = name

    #index_values = convert_index(df.index)
    #rows = izip(index_values, df.open, df.high, df.low, df.close, df.vol)

    # TODO this is fast but can't support multiindex
    table.append(df.to_records())

    hfile.flush()

def table_to_frame(table):
    columns = table.attrs.pandas_columns
    index_name = table.attrs.pandas_index_name
    index_type = table.attrs.pandas_index_type
    name = table.attrs.pandas_name

    index_values = table.col(index_name)
    index = unconvert_index(index_values, index_type)

    data = {}
    for col in columns:
        data[col] = table.col(col)

    df = pd.DataFrame(data, columns=columns, index=index)
    df.name = name
    return df
