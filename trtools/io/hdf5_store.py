from trtools.io.pytables import HDF5Handle, convert_frame, frame_to_table
from trtools.io.panda_hdf import OneBigTable, create_obt

def hdf_save(obj, filename):
    try:
        hdf = SingleHDF(filename, 'w')
        hdf.save(obj)
    finally:
        hdf.handle.close()

def hdf_open(obj, filename):
    try:
        hdf = SingleHDF(filename, 'r')
        hdf.save(obj)
    finally:
        hdf.handle.close()

class SingleHDF(object):
    """
    HDF that stored a single DataFrame
    """
    def __init__(self, filename, mode='a'):
        self.filename = filename
        self.handle = HDF5Handle(filename, mode)

    def save(self, obj):
        group = self.handle.create_group('data')
        expectedrows = len(obj)
        group.frame_to_table(obj, name='data_table', expectedrows=expectedrows)

    def load(self):
        return self.handle.data['data_table'][:]

    def __repr__(self):
        return repr(self.handle)

class SingleOBT(object):
    def __init__(self, filename, mode='a', frame_key=None):
        self.filename = filename
        self.mode = mode
        self.handle = HDF5Handle(filename, mode)
        self.frame_key = self.get_frame_key(frame_key)

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

    def create_table(self, df):
        OBT = create_obt(self.handle.root, 'obt', df, 'symbol')
        self._obt = OBT

    def close(self):
        self.handle.close()

    def __setitem__(self, key, value):
        if self.obt is None:
            self.create_table(value)
        self.obt[key] = value

    def append(self, value):
        if self.obt is None:
            self.create_table(value)
        self.obt.append(value)
