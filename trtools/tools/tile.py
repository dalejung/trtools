
import operator

from pandas import cut, Series, DataFrame, Categorical
import numpy as np

from trtools.monkey import patch

inf = 9999999999

inf_trans = lambda x: x == inf and 'inf' or x == -inf and '-inf' or x

class NumRange(object):
    def __init__(self, l, h):
        self.l = l
        self.h = h

    def __repr__(self):
        l, h = (self.l, self.h)
        l = inf_trans(l)
        h = inf_trans(h)
        return "[%s, %s]" % (l, h)

    def __float__(self):
        if self.l == inf:
            return self.h
        if self.h == inf:
            return self.l
        return (self.l + self.h) / 2

    def _cmp(self, other, op):
        try:
            return op(self.l, other.l)
        except:
            if op in [operator.ne, operator.gt, operator.lt]:
                return True
            return False

    __eq__  = lambda self, other: self._cmp(other, operator.eq)
    __ne__  = lambda self, other: self._cmp(other, operator.ne)
    __lt__  = lambda self, other: self._cmp(other, operator.lt)
    __le__  = lambda self, other: self._cmp(other, operator.le)
    __gt__  = lambda self, other: self._cmp(other, operator.gt)
    __ge__  = lambda self, other: self._cmp(other, operator.ge)

    def __hash__(self):
        return hash((self.l, self.h))

def _tile_inds(s, bins, labels=False, retbins=True, infinite=True):
    #  NOTE: inf only happens when explicitly setting bins

    # short circuit empty series
    s = Series(s)
    if s.count() == 0:
        return np.repeat(None, len(s))

    if not np.iterable(bins):
        ind, label = cut(s, bins, retbins=retbins, labels=labels)
        # for now, pandas base cut doesn't support infinite ranges
        # so it bases first bin at 0 where we base on 1, and 0 is 
        # [-inf, first] for us
        ind = ind + 1
    else:
        bins = np.asarray(bins)
        #if (np.diff(bins) < 0).any():
        #    raise ValueError('bins must increase monotonically.')
        ind, label = inf_bins_to_cuts(s, bins)
    

    # build out ranges
    ranges = []
    ranges.append(NumRange(-inf, label[0]))
    for x in range(len(label)-1):
       nr = NumRange(label[x], label[x+1]) 
       ranges.append(nr)
    ranges.append(NumRange(label[-1], inf))

    if not infinite:
        na_mask = (ind == 0) | (ind == len(bins))
        np.putmask(ind, na_mask, -1)

    #ind = ind.astype(int)
    ind[s.isnull().values] = -1
    return Categorical(ind, ranges)

def tile(s, bins, labels=False, retbins=True, infinite=True):
    new_index = _tile_inds(s, bins, labels=labels, retbins=retbins, infinite=infinite)
    grouped = s.groupby(new_index, sort=True)
    return grouped



def inf_bins_to_cuts(x, bins, right=True, retbins=True,
                  precision=3, name=None, include_lowest=False):
    """
        Cut bins while supporting infinite. 
        Regular pd.cut replaces out of range with nan. We support
        positive and negative inf so you know which direction the value 
        laid out. 
    """
    if name is None and isinstance(x, Series):
        name = x.name
    x = np.asarray(x)

    side = 'left' if right else 'right'
    ids = bins.searchsorted(x, side=side)

    if include_lowest:
        ids[x == bins[0]] = 1

    fac = ids
    fac = fac.astype(np.float64)

    if not retbins:
        return fac

    return fac, bins

@patch(Series, 'tile')
def tile_series(self, bins, series=None):
    return tile(self, bins)

@patch(DataFrame, 'tile')
def tile_df(self, bins, col):
    series = self[col]
    ind = _tile_inds(series, bins)
    return self.groupby(ind)

