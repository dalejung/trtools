import cPickle as pickle
import os.path

class CachingDict(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self._dict = {}

        self.load()

    def keys(self):
        return self._dict.keys()

    def __setitem__(self, key, value):
        self._dict.__setitem__(key, value)
        self.save()

    def __getitem__(self, key):
        return self._dict.__getitem__(key)

    def load(self):
        if os.path.isfile(self.filepath):
            obj = pickle.load(open(self.filepath))
            self._dict = obj

    def save(self):
        with open(self.filepath, 'wb') as f:
            pickle.dump(self, f)
