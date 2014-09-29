import os.path
import glob

from trtools.io.filecache import FileCache, _filename, leveled_filename
from trtools.io.hdf5_grouping import HDFPanel

class SingleHDF(object):
    """
    Methods for writing each result as it's own hdf
    """
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
        keys = list(super(HDF5FileCache, self).keys())
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
    """
        The idea originally was to have a context that closed handle on exit.
        To minimize possible data corruption. 
    """
    def __init__(self, filename, frame_key=None, filters=None, expectedrows=None):
        self.filename = filename
        self.frame_key = frame_key
        self.filters = filters
        self.hdf = None
        self.expectedrows = expectedrows

    def open(self):
        if not (self.hdf and self.hdf.handle.isopen):
            hdf = HDFPanel(self.filename, 'a')
            self.hdf = hdf
        return self.hdf

    def __enter__(self):
        hdf = self.open()
        if not hasattr(hdf.handle.root, 'obt'):
            hdf.create_obt('obt', frame_key=self.frame_key, filters=self.filters, 
                          expectedrows=self.expectedrows)
        obt = hdf['obt']
        return obt

    def __exit__(self, exc_type, exc_value, traceback):
        #self.hdf.handle.close()
        pass

class OBTFileCache(object):
    def __init__(self, cache_file, frame_key=None, filters=None, expectedrows=None, 
                 append_only=False, *args, **kwargs):
        self.filters = filters
        self.cache_file = cache_file
        self.check_dir()
        self.frame_key = frame_key
        self.obt_context = OBTContext(self.cache_file, self.frame_key, expectedrows=expectedrows)
        self.append_only = append_only

    def check_dir(self):
        dir = os.path.dirname(self.cache_file)
        if not os.path.isdir(dir):
            os.makedirs(dir)

    def __setitem__(self, key, value):
        with self.obt_context as obt:
            if self.append_only:
                obt.append(value)
            else:
                obt[key] = value

    def __getitem__(self, key):
        with self.obt_context as obt:
            return obt[key]

    def keys(self):
        with self.obt_context as obt:
            try:
                return list(obt.keys())
            except:
                return []

    def sortby(self, key):
        # TODO use table.copy to reorder the data
        pass

    def delete_all(self):
        with self.obt_context as obt:
            obt.group._f_remove(recursive=True)

    @property
    def sql(self):
        with self.obt_context as obt:
            return obt.sql

    @property
    def hdf(self):
        with self.obt_context:
            return self.obt_context.hdf

    @property
    def obt(self):
        with self.obt_context as obt:
            return obt
