import os.path
import glob

from trtools.io.filecache import FileCache, _filename, leveled_filename
from trtools.io.pytables import HDFPanel

class SingleHDF(object):

    @staticmethod
    def put(filename, obj, filters=None):
        panel = HDFPanel(filename, 'w')
        with panel.handle:
            gr = panel.create_group('data', filters=filters)
            gr['data'] = obj

    @staticmethod
    def get(filename):
        panel = HDFPanel(filename, 'r')
        with panel.handle:
            gr = panel['data']
            df = gr['data'] 
        return df

class HDF5FileCache(FileCache):
    def __init__(self, cache_dir, filename_func=None, filters=None, *args, **kwargs):
        self.filters = filters
        super(HDF5FileCache, self).__init__(cache_dir, filename_func, *args, **kwargs)

    def get_filename(self, name):
        name = _filename(name) + '.h5'
        filename = os.path.join(self.cache_dir, name)
        return filename

    def put(self, name, obj):
        filename = self.get_filename(name)
        SingleHDF.put(filename, obj, filters=self.filters)

    def get(self, name):
        filename = self.get_filename(name)
        return SingleHDF.get(filename)

    def keys(self):
        keys = super(HDF5FileCache, self).keys()
        return [filename[:-3] for filename in keys]

class HDF5LeveledFileCache(HDF5FileCache):
    def __init__(self, cache_dir, length=1, *args, **kwargs):
        self.length = length
        super(HDF5LeveledFileCache, self).__init__(cache_dir, *args, **kwargs) 

    def get_filename(self, name):
        filename = leveled_filename(fc=self, name=name, length=self.length)
        return filename + ".h5"

    def keys(self):
        pat = self.cache_dir + '/*/*'
        files = glob.glob(pat)
        keys =  [os.path.basename(f) for f in files]
        return [filename[:-3] for filename in keys]

class OBTContext(object):
    def __init__(self, filename, frame_key=None, filters=None):
        self.filename = filename
        self.frame_key = frame_key
        self.filters = filters
        self.hdf = None

    def open(self):
        if not (self.hdf and self.hdf.handle.isopen):
            hdf = HDFPanel(self.filename, 'a')
            self.hdf = hdf
        return self.hdf

    def __enter__(self):
        hdf = self.open()
        if not hasattr(hdf.handle.root, 'obt'):
            hdf.create_obt('obt', frame_key=self.frame_key, filters=self.filters)
        obt = hdf['obt']
        return obt

    def __exit__(self, exc_type, exc_value, traceback):
        #self.hdf.handle.close()
        pass

class OBTFileCache(object):
    def __init__(self, cache_file, frame_key=None, filters=None, *args, **kwargs):
        self.filters = filters
        self.cache_file = cache_file
        self.frame_key = frame_key
        self.obt = OBTContext(self.cache_file, self.frame_key)

    def __setitem__(self, key, value):
        with self.obt as obt:
            obt[key] = value

    def __getitem__(self, key):
        with self.obt as obt:
            return obt[key]

    def keys(self):
        with self.obt as obt:
            try:
                return obt.keys()
            except:
                []

    def delete_all(self):
        with self.obt as obt:
            obt.group._f_remove(recursive=True)

    @property
    def sql(self):
        with self.obt as obt:
            return obt.sql