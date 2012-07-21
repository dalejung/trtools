import os

import pandas as pd

class FileCache(object):
    """
        Basically a replacement for the HDF5Store. It stores as flat files.
    """
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self._create_dir()

    def _create_dir(self):
        dir = self.cache_dir
        if not os.path.exists(dir):
            os.makedirs(dir)

    def get_filename(self, name):
        filename = os.path.join(self.cache_dir, name)
        return filename

    def put(self, name, obj):
        filename = self.get_filename(name)
        pd.save(obj, filename)

    def get(self, name):
        filename = self.get_filename(name)
        obj = pd.load(filename)
        obj.name = name
        return obj

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.put(key, value)

    def __contains__(self, key):
        filename = os.path.join(self.cache_dir, key)
        return os.path.exists(filename)

    def __len__(self):
        return len(self.keys())

    def __repr__(self):
        output = '%s\nCache path: %s\n' % (type(self), self.cache_dir)

        if len(self) > 0:
            output += '\n'.join(self.keys())
        else:
            output += 'Empty'

        return output

    def keys(self):
        dir = self.cache_dir
        keys = os.listdir(dir)
        return keys
