"""
    Purpose of PandasDB is to create a persistent database like object that 
    also keeps a log. 

    Rather not deal with sqlite db
"""
import pandas as pd

import trtools.tools.io as tio

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

    def reset(self, df):
        self.init_df(df)

    def _init_df(self, data):
        """
            Load df from buffer and set
        """
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            print('loading from cache')
            df = tio.load(data)
        self._df = df

    def init_df(self, data):
        """
            Load df from buffer and set
        """
        self._init_df(data) 
        self.save()

    def load(self, f=None):
        f = f or self._get_fp('rb')
        self._df = tio.load(f)

    def save(self, f=None):
        f = f or self._get_fp('wb')
        tio.save(self._df, f)

    def _get_fp(self, mode='rb'):
        return open(self.filepath, mode)

    def __getattr__(self, name):
        if name in self._df.columns:
            return self._df[name]
        raise AttributeError(name)

    def __getstate__(self): return self.__dict__
    def __setstate__(self, d): self.__dict__.update(d)

    @property
    def df(self):
        return self._df

    @property
    def sql(self):
        return self._df.sql

    @property
    def cols(self):
        return self._df.cols

    def query(self):
        return self._df.sql.query()

    def filter(self, *args, **kwargs):
        return self.query().filter(*args, **kwargs)

    def __repr__(self):
        return repr(self._df)

