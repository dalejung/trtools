import numpy as np

import pandas as pd

from tables import openFile

from trtools.io.pytables import _meta, HDFSql, table_to_frame, frame_to_table, \
                                _convert_param, HDFQuery, convert_frame

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

    def __getattr__(self, key):
        if hasattr(self.handle, key):
            return getattr(self.handle, key)
        raise AttributeError()

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

    def create_group(self, group_name, filters=None):
        """
            Create HDFPanelGroup
        """
        handle = self.handle    
        group = handle.createGroup(handle.root, group_name, group_name, filters=filters)

        meta = {}
        meta['group_type'] = 'panel'

        _meta(group, meta)

        return HDFPanelGroup(group, self, filters=filters)

    def create_obt(self, group_name, frame_key=None, table_name=None, filters=None,
                  expectedrows=None):
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
        meta['expectedrows'] = expectedrows

        _meta(group, meta)

        return OBTGroup(group, self, filters=filters, **meta)

class HDFPanelGroup(object):
    pd_group_type = 'panel_group'

    def __init__(self, group, panel, *args, **kwargs):
        self.group = group
        self.panel = panel
        self.filters = kwargs.pop('filters', None)

    def __getattr__(self, key):
        if hasattr(self.group, key):
            return getattr(self.group, key)
        raise AttributeError()

    def meta(self):
        return _meta(self.group)

    def get_table(self, name):
        group = self.group
        if hasattr(group, str(name)):
            return getattr(group, str(name))

        raise Exception("{0} does not exist in this Group".format(name))

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

    def create_table(self, df, name=None, *args, **kwargs):
        filters = self.filters
        table = frame_to_table(name, df, self.group, filters=filters, 
                               *args, **kwargs)
        return table

    def append(self, df, name=None):
        self._append(df, name)

    def _append(self, df, name=None):
        table = self.get_table(name)
        desc, recs, types = convert_frame(df)
        table.append(recs)
        table.flush()

    def __setitem__(self, key, value):
        self.create_table(value, name=key)

    def __getitem__(self, key):
        return self.get_data(key)

    def foreach(self, func):
        pass
        # call func on each node

class OBTGroup(HDFPanelGroup):
    def __init__(self, group, panel, frame_key, table_name, copy=True, 
                 expectedrows=None, *args, **kwargs):
        super(OBTGroup, self).__init__(group, panel, *args, **kwargs)

        self.frame_key = frame_key
        self.table_name = table_name
        self._table = None
        self.copy = copy
        # having this kind of hacky expectedrows pass through is because
        # there isn't an explicit tabel creation step. It does it
        # automagically on first __setitem__. Which might be a mistake for 
        # OBT. Makes sense for non-OBT. HMMM.
        self.expectedrows = expectedrows

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
            self.append(df)
        else:
            # to create table we need some data to infer type
            if len(df) == 0:
                return
            table = self.create_table(df, name=table_name, expectedrows=self.expectedrows)
            self._table = table

    def append(self, df):
        # to create table we need some data to infer type
        if len(df) == 0:
            return

        table_name = self.table_name
        if hasattr(self.group, table_name):
            self._append(df, name=table_name)
        else:
            table = self.create_table(df, name=table_name, expectedrows=self.expectedrows)
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
        # return in a form that's more useful. considering outputting panel
        return df.pivot(df.index, self.frame_key).stack().to_panel()

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

    def index_default(self):
        table_meta = _meta(self.table)
        index_name = table_meta['index_name']
        self.add_index(index_name)
        self.add_index(self.frame_key)

