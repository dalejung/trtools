import pandas as pd

from trtools.monkey import patch

import trtools.tools.composition as composition

def _get_meta(obj):
    # _get grabs from the obj itself and not it's pobj
    getter = getattr(obj, '_get', None)
    meta = {}
    if callable(getter):
        d = getter('__dict__')
        meta.update(d)
    meta.update(getattr(obj, '__dict__', {}))
    meta.pop('_index', None) # don't store index
    meta.pop('pobj', None) # don't store pobj
    return meta

class DataSet(composition.UserFrame):
    """
        DataSet is a UserFrame that retains the class
        and metadata of its series. 
    """
    _col_classes = {}
    _col_meta = {}

    def __setitem__(self, key, val):
        # just do isinstance(pd.Series) check?
        if hasattr(val, '__dict__'):
            d = _get_meta(val).copy()
            self._col_meta[key] = d
            self._col_classes[key] = type(val) 
        super(DataSet, self).__setitem__(key, val)

    def _wrap_series(self, key):
        ret = super(DataSet, self).__getitem__(key)
        ret = ret.view(self._col_classes[key])
        meta = self._col_meta[key]
        ret.__dict__.update(meta)
        return ret

    def __getitem__(self, key):
        if key in self.columns:
            return self._wrap_series(key)
        raise AttributeError(key)

    def __tr_getattr__(self, key):
        return self[key]

@patch(pd.DataFrame, 'dataset')
def dataset(self):
    return DataSet(index=self.index)
