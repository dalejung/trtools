import os.path
import glob

from trtools.io.filecache import FileCache, _filename, leveled_filename
from trtools.io.pytables import HDFPanel

class SingleHDF(object):

    @staticmethod
    def put(filename, obj):
        panel = HDFPanel(filename, 'w')
        with panel.handle:
            gr = panel.create_group('data')
            gr['data'] = obj

    @staticmethod
    def get(filename):
        panel = HDFPanel(filename, 'r')
        with panel.handle:
            gr = panel['data']
            df = gr['data'] 
        return df

class HDF5FileCache(FileCache):
    def get_filename(self, name):
        name = _filename(name) + '.h5'
        filename = os.path.join(self.cache_dir, name)
        return filename

    def put(self, name, obj):
        filename = self.get_filename(name)
        SingleHDF.put(filename, obj)

    def get(self, name):
        filename = self.get_filename(name)
        return SingleHDF.get(filename)

class HDF5LeveledFileCache(HDF5FileCache):
    def __init__(self, cache_dir, length=1):
        self.length = length
        super(HDF5LeveledFileCache, self).__init__(cache_dir) 

    def get_filename(self, name):
        filename = leveled_filename(fc=self, name=name, length=self.length)
        return filename + ".h5"

    def keys(self):
        pat = self.cache_dir + '/*/*'
        files = glob.glob(pat)
        return [os.path.basename(f) for f in files]
