from trtools.monkey import patch
import pandas as pd

@patch(pd.Series, 'true')
def true(self):
    """
        Return the True values of a series
    """
    return self[self]
