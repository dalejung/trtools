import pandas as pd
import numpy as np

from trtools.io.pytables import convert_frame, _meta, copy_table_def, SimpleIndexer

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
            # have we sorted by index?
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

    _ix = None
    @property
    def ix(self):
        if self._ix is None:
            self._ix = SimpleIndexer(self)
        return self._ix

    def __getattr__(self, key):
        if hasattr(self.table, key):
            return getattr(self.table, key)
        raise AttributeError()

    def __getitem__(self, key):
        if isinstance(key, basestring):
            return self._getitem_framekey(key)
        if isinstance(key, int):
            return self._getitem_framekey(key)
        df = self.table[key]
        df.set_index(self.frame_key, append=True, inplace=True)
        return df

    def _getitem_framekey(self, key):
        query = getattr(self.table.sql, self.frame_key) == key
        df = self.table[query]
        del df[self.frame_key]
        return df

    def index_default(self):
        table_meta = _meta(self.table)
        index_name = table_meta['index_name']
        self.table.add_index(index_name)
        self.table.add_index(self.frame_key)

    def sort_index(self):
        df = self.table[:] # getitem returns MultiIndex
        df = df.sort_index()
        table = copy_table_def(self.group, 'indexed_table', self.table)
        table.append(df)

        self._table = None

def create_obt(parent, name, df, frame_key, frame_key_sample=None, expectedrows=None):
    template = df.ix[0:1].copy()
    # default to string frame_eky
    if frame_key_sample is None:
        frame_key_sample = ""
    if frame_key not in template.columns:
        template[frame_key] = frame_key_sample

    meta = {'group_type':'obt', 'frame_key':frame_key}
    group = parent.create_group(name, meta=meta) 
    columns=list(template.columns)

    table = group.frame_to_table('obt', template, expectedrows=expectedrows, create_only=True)

    OBT = OneBigTable(group, frame_key)
    return OBT
