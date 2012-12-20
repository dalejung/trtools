from StringIO import StringIO
import time

import numpy as np
import pandas as pd
from pandas.util.testing import *

class TestStringIO(StringIO):
    def close(self):
        pass

    def free(self):
        StringIO.close(self)

class Timer:
    """
        Usage:

        with Timer() as t:
            ret = func(df)
        print(t.interval)
    """
    def __init__(self, name='', verbose=True):
        self.name = name
        self.verbose = verbose

    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start
        if self.verbose:
            print "Run {0}: {1}".format(self.name, self.interval)

def fake_ohlc(N=1000, start="2000/01/01", freq="D"):
    """
        Meh, need to make this better behaved
    """
    ind = pd.date_range(start, freq=freq, periods=N)
    returns = (np.random.random(N) - .5) * .05
    geom = (1+returns).cumprod()

    open = 100 * geom
    close = open + (open * (np.random.random(N) - .5)) * .1
    high = np.maximum(open, close)
    low = np.minimum(open, close)

    df = pd.DataFrame(index=ind)
    df['open'] = open
    df['high'] = high
    df['low'] = low
    df['close'] = close
    return df
