import pandas as pd

from trtools.monkey import patch

import trtools.tools.composition as composition


class DataSet(composition.UserFrame):
    pass

@patch(pd.DataFrame, 'dataset')
def dataset(self):
    return DataSet(index=self.index)
