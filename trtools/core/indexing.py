import numpy as np
import pandas as pd

from trtools.monkey import patch

@patch(pd.MultiIndex)
def to_frame(self):
    """
    Change a MultiIndex to a DataFrame with get level values
    corresponding to a column

    I could just reset_index on the DataFrame, but I keep on forgetting...
    """
    names = [name or i for i, name in enumerate(self.names)]
    data = {name:self.get_level_values(i) for i, name in enumerate(names)}
    return pd.DataFrame(data, columns=names)
