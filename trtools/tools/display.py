import pandas as pd

def mush(left, right, columns=None, suffix="_right"):
    """
       Will take two dataframes and combine them. It is assumed that the right
       dataframe is derivative of the left, thus having the same index and columns. 

    """
    if columns is None:
        columns = right.columns

    # hack to handle columns that are objects. 
    # i.e. Stock class can match integers, which pandas will treat as 
    # integer positions
    columns = [col for col in left.columns if col in columns]

    left = left.ix[:, columns]
    right = right.ix[:, columns]
    df = pd.merge(left, right, right_index=True, left_index=True, suffixes=('', suffix))
    df = df.sort(axis=1)
    return df
