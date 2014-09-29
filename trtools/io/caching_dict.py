from contextlib import closing

from trtools.compat import pickle

class CachingDict(object):
    """
        Essentially a dict that writes itself to disk everytime an
        item is set
    """
    def __init__(self, filepath):
        self.filepath = filepath
        self._dict = {}

        self.load()

    def keys(self):
        return list(self._dict.keys())

    def update(self, *args, **kwargs):
        self._dict.update(*args, **kwargs)
        self.save()

    def __setitem__(self, key, value):
        self._dict.__setitem__(key, value)
        self.save()

    def __getitem__(self, key):
        return self._dict.__getitem__(key)

    def __delitem__(self, key):
        self._dict.__delitem__(key)
        self.save()

    def load(self):
        try:
            obj = pickle.load(self.get_fp())
            self._dict = obj
        except:
            pass

    def get_fp(self, mode='rb'):
        """
            Factored out for testing purposes
        """
        return open(self.filepath, mode)

    def save(self):
        with closing(self.get_fp('wb')) as f:
            pickle.dump(self, f)

    def clear(self):
        self._dict.clear()
        self.save()

    def __contains__(self, key):
        return key in self._dict

    def __len__(self):
        return len(list(self.keys()))
