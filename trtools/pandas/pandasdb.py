"""
    Purpose of PandasDB is to create a persistent database like object that 
    also keeps a log. 

    Rather not deal with sqlite db
"""
import pandas as pd

import trtools.pandas.pandassql as pdsql
import trtools.io as tio

class PandasDB(object):
    pass

class PandasTable(object):
    """
        Pandas Table corresponds to one DataFrame
    """
    def __init__(self, filepath):
        self._df = None
        self.filepath = filepath

        try:
            self.load()
        except:
            pass

    def init_df(self, data):
        """
            Load df from buffer and set
        """
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            df = tio.load(data)
        self._df = df
        self.save()

    def load(self, f=None):
        f = f or self._get_fp('rb')
        self._df = tio.load(f)

    def save(self, f=None):
        f = f or self._get_fp('wb')
        tio.save(self, f)

    def _get_fp(self, mode='rb'):
        return open(self.filepath, mode)

    def __getattr__(self, name):
        if name in self._df.columns:
            return self._df[name]
        raise AttributeError(name)

    def __getstate__(self): return self.__dict__
    def __setstate__(self, d): self.__dict__.update(d)

    @property
    def sql(self):
        return self._df.sql
