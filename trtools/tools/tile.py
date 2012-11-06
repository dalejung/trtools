from __future__ import division

from pandas import cut, Series, DataFrame
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

    __eq__  = lambda self, other: self.l == other.l
    __ne__  = lambda self, other: self.l != other.l
    __lt__  = lambda self, other: self.l < other.l
    __le__  = lambda self, other: self.l <= other.l
    __gt__  = lambda self, other: self.l > other.l
    __ge__  = lambda self, other: self.l >= other.l

    def __hash__(self):
        return hash((self.l, self.h))

def tile(s, bins, labels=False, retbins=True, infinite=True):
    # 
    if not np.iterable(bins):
        ind, label = cut(s, bins, retbins=retbins, labels=labels)
        # for now, pandas base cut doesn't support infinite ranges
        # so it bases first bin at 0 where we base on 1, and 0 is 
        # [-inf, first] for us
        ind = ind + 1
    else:
        bins = np.asarray(bins)
        if (np.diff(bins) < 0).any():
            raise ValueError('bins must increase monotonically.')
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
        np.putmask(ind, na_mask, np.nan)

    # redo the intindex as range index
    new_index = ind.astype(object)
    ind = Series(ind)


    for k, v in ind.dropna().astype(int).iteritems():
        newr = ranges[v]
        new_index[k] = newr

    grouped = s.groupby(new_index, sort=True)
    return grouped


def inf_bins_to_cuts(x, bins, right=True, retbins=True,
                  precision=3, name=None, include_lowest=False):
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
    ind = cut(series, bins)
    return self.groupby(ind)

