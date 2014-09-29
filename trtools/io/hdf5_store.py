import os
import shutil

from trtools.io.pytables import HDF5Handle, convert_frame, frame_to_table
from trtools.io.panda_hdf import OneBigTable, create_obt

def hdf_save(obj, filename):
    try:
        hdf = HDFFile(filename, 'w')
        hdf.save(obj)
    finally:
        hdf.handle.close()

def hdf_open(obj, filename):
    try:
        hdf = HDFFile(filename, 'r')
        hdf.save(obj)
    finally:
        hdf.handle.close()

class HDFFile(object):
    """
    HDF that stored a single DataFrame
    """
    def __init__(self, filename, mode='a', expectedrows=None, type=None):
        self.dir = filename
        if os.path.isdir(self.dir) and mode == 'w':
            shutil.rmtree(self.dir)
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
        fn = os.path.basename(filename)
        self.filename = os.path.join(filename, fn)
        self.handle = HDF5Handle(self.filename, mode, type=type)
        self.expectedrows = expectedrows

    _table = None
    @property
    def table(self):
        if self._table is None and hasattr(self.handle, 'data'):
            if hasattr(self.handle.data, 'data_table'):
                self._table = self.handle.data.data_table
        return self._table

    def create_table(self, df, expectedrows=None, create_only=False):
        expectedrows = expectedrows or self.expectedrows
        group = self.handle.create_group('data')
        group.frame_to_table('data_table', df, expectedrows=expectedrows, 
                             create_only=create_only)

    def save(self, obj):
        expectedrows = len(obj)
        self.create_table(obj, expectedrows=expectedrows)

    def load(self):
        return self.handle.data['data_table'][:]

    def __repr__(self):
        return repr(self.handle)

    def __setitem__(self, key, value):
        self.append(value)

    def append(self, value, flush=True):
        if self.table is None:
            self.create_table(value, create_only=True)
        self.table.append(value, flush=flush)

    def close(self):
        self.handle.close()

class OBTFile(object):
    def __init__(self, filename, mode='a', frame_key=None, expectedrows=None, type=None):
        self.filename = filename
        dir = os.path.dirname(filename)
        if not os.path.isdir(dir):
            os.makedirs(dir)

        self.mode = mode
        self.handle = HDF5Handle(filename, mode, type=type)
        self.frame_key = self.get_frame_key(frame_key)

        self.expectedrows = expectedrows

        if self.obt is None and mode == 'r':
            raise Exception("Opening Empty File in mode r")

    _obt = None
    @property
    def obt(self):
        if self._obt is None:
            if hasattr(self.handle, 'obt'):
                self._obt = OneBigTable(self.handle.obt)
        return self._obt

    def get_frame_key(self, frame_key):
        if frame_key:
            return frame_key
    
        if self.obt is None:
            raise Exception("Empty OBT with no frame_key specified")
        frame_key = self.obt.frame_key
        return frame_key

    def create_table(self, df, key=None):
        OBT = create_obt(self.handle.root, 'obt', df, self.frame_key,
                         frame_key_sample=key, expectedrows=self.expectedrows)
        self._obt = OBT

    def close(self):
        self.handle.close()

    def __setitem__(self, key, value):
        if self.obt is None:
            self.create_table(value, key=key)
        # setitem creates the frame_key column, which isnt always needed
        if self.frame_key in value.columns:
            self.obt.append(value)
        else:
            self.obt[key] = value

    def append(self, value):
        if self.obt is None:
            self.create_table(value)
        self.obt.append(value)

    def __getattr__(self, key):
        if hasattr(self.obt, key):
            return getattr(self.obt, key)
        raise AttributeError()

    def keys(self):
        if self.obt is None:
            return []
        return list(self.obt.keys())
