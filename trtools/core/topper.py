import bottleneck as nb
import pandas as pd
import numpy as np

from trtools.monkey import patch

def top_x(df, max=10, ascending=True):
    """
    Returns a grid with columns being order position and values being 
    the df.columns
    """
    def topper(s):
        ret = pd.Series(index=range(max))
        data = s.order(ascending=ascending)[:max].index
        ret[range(len(data))] = data
        return ret
    return df.apply(topper, axis=1)

def bn_topn(arr, N, ascending=True):
    """
    Return the top N results. Negative N will give N lowest results

    Paramters
    ---------
    arr : Series
        one dimension array
    N : int
        number of elements to return. Negative numbers will return smallest
    ascending : bool
        Ordering of the return values. Default to True

    Note
    ----
    Results are ordered smallest-to-largest regardless if you grab
    from bottom or top. Use `ascending` param to change sort order
    """
    arr = arr[~np.isnan(arr)]
    if N > 0: # nlargest
        N = len(arr) - abs(N)
        sl = slice(N, None)
    else: # nsmallest
        N = abs(N)
        sl = slice(None, N)
    out = nb.partsort(arr, N)
    bn_res = out[sl]
    bn_res = np.sort(bn_res) # sort output
    if not ascending:
        bn_res = bn_res[::-1]
    return bn_res

def bn_topargn(arr, N, ascending=True):
    """
    Return the indices of the top N results. 
    The following should be equivalent

    >>> res1 = arr[bn_topargn(arr, 10)] 
    >>> res2 = bn_topn(arr, 10)
    >>> np.all(res1 == res2)
        True
    """
    na_mask = np.isnan(arr)
    has_na = na_mask.sum()
    if has_na:
        # store the old indices for translating back later
        old_index_map = np.where(~na_mask)[0]
        arr = arr[~na_mask]

    if N > 0: # nlargest
        N = len(arr) - abs(N)
        sl = slice(N, None)
    else: # nsmallest
        N = abs(N)
        sl = slice(None, N)
    out = nb.argpartsort(arr, N)
    index = out[sl]
    # sort the index by their values
    index_sort = np.argsort(arr[index])
    if not ascending:
        index_sort = index_sort[::-1]
    index = index[index_sort]

    # index is only correct with arr without nans. 
    # Map back to old_index if needed
    if has_na:
        index = old_index_map[index]
    return index

topn = bn_topn
topargn = bn_topargn

@patch(pd.Series, 'topn')
def _topn_series(self, N, ascending=True):
    return topn(self, N, ascending=ascending)

@patch(pd.Series, 'topargn')
def _topargn_series(self, N, ascending=True):
    return topargn(self, N, ascending=ascending)
