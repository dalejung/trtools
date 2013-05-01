from trtools.monkey import patch
import pandas as pd

@patch(pd.Series, 'true')
def true(self):
    """
        Return the True values of a series
    """
    return self[self]

@patch(pd.DataFrame, 'isnull')
def isnull(self):
    return pd.isnull(self)

@patch(pd.DataFrame, 'notnull')
def notnull(self):
    return pd.notnull(self)
