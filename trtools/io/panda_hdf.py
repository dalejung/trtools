import pandas as pd
import numpy as np

from trtools.io.pytables import convert_frame, _meta

def copy_table_def(group, name, orig):
    table_meta = _meta(orig)
    desc = orig.description
    types = table_meta['value_types']
    index_name = table_meta['index_name']
    columns = table_meta['columns']
    expectedrows = orig.nrows
    table = group.create_table(name, desc, types, columns=columns, index_name=index_name, expectedrows=expectedrows)
    return table

class OneBigTable(object):
    """
        This wraps around a pytable Table
    """
    def __init__(self, group, frame_key=None):
        self.group = group
        meta = self.group.meta()
        self.frame_key = frame_key or meta['frame_key']
        self._table = None

    @property
    def table(self):
        if self._table is None:
            if hasattr(self.group, 'indexed_table'):
                self._table = getattr(self.group, 'indexed_table')
            else:
                self._table = self.group['obt']
        return self._table

    def __setitem__(self, key, value):
        # TODO This should be like mode 'w'. Where another method will be the append
        # Right now it will just append to the same frame_key
        ind = value.index
        if isinstance(value, pd.Series):
            value = {'vals': value}

        # we copy cuz we add the frame_key to the dataframe
        df = pd.DataFrame(value, index=ind, copy=True) 
        df[self.frame_key] = key

        self.append(df)

    def append(self, df):
        # to create table we need some data to infer type
        if len(df) == 0:
            return

        self.table.append(df)

    def keys(self):
        data = self.table.col(self.frame_key)
        return list(np.unique(data))

    @property
    def index(self):
        return self.table.index

    def __getitem__(self, key):
        return self.table[key]

    def index_default(self):
        table_meta = _meta(self.table)
        index_name = table_meta['index_name']
        self.table.add_index(index_name)
        self.table.add_index(self.frame_key)

    def sort_index(self):
        df = self[:]
        df = df.sort_index()
        table = copy_table_def(self.group, 'indexed_table', self.table)
        table.append(df)

def create_obt(parent, name, df, frame_key, frame_key_sample="", expectedrows=None):
    template = df.ix[0:1].copy()
    if frame_key not in template.columns:
        template[frame_key] = frame_key_sample
    conv = convert_frame(template)
    desc = conv[0]
    types = conv[2]
    meta = {'group_type':'obt', 'frame_key':frame_key}
    group = parent.create_group(name, meta=meta) 
    columns=list(template.columns)

    table = group.create_table('obt', desc, types, columns=columns, index_name='pd_index', 
                               expectedrows=expectedrows)

    OBT = OneBigTable(group, frame_key)
    return OBT
