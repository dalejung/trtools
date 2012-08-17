"""
    Just tools to help with R and quantmod. 
"""
import pandas as pd

def col_grep(df, name, single=True):
    """
        Return column names matching a case insensitive search
    """
    columns = df.columns
    ret = []
    for col in columns:
        if name in col.lower():
            if single:
                return col
            ret.append(col)
    return ret

Op = lambda df: df[col_grep(df, 'open')]
Hi = lambda df: df[col_grep(df, 'high')]
Lo = lambda df: df[col_grep(df, 'low')]
Cl = lambda df: df[col_grep(df, 'close')]
Vo = lambda df: df[col_grep(df, 'volume')]

def normalize_ohlc(df, copy=True):
    # copy only the ohlc parts of a df
    # might want make a wrapper version where copy = False
    if not copy:
        raise Exception("Haven't built non copy version")

    ohlc_df = pd.DataFrame({'open': Op(df), 'high': Hi(df), 'low': Lo(df), 
                            'close': Cl(df), 'volume': Vo(df)}, index=df.index)
    return ohlc_df
