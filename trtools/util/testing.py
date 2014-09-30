import time

import numpy as np
import pandas as pd
from pandas.util.testing import *

from trtools.compat import StringIO, BytesIO
from trtools.core.api import ColumnPanel

class TestStringIO(BytesIO):
    def close(self):
        pass

    def free(self):
        BytesIO.close(self)

class Timer:
    """
        Usage:

        with Timer() as t:
            ret = func(df)
        print(t.interval)
    """
    runs = []

    def __init__(self, name='', verbose=True):
        self.name = name
        self.verbose = verbose
        self.start = None
        self.wall_start = None
        self.end = None
        self.wall_end = None
        Timer.runs.append(self)

    def clear_runs(self):
        Timer.runs = []

    def __enter__(self):
        self.start = time.clock()
        self.wall_start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.wall_end = time.time()
        self.interval = self.end - self.start
        self.wall_interval = self.wall_end - self.wall_start

        if self.verbose:
            print((self.msg))

    @property
    def msg(self):
        msg = "Run {name}: CPU time: {interval}  Wall time: {wall_interval}"
        return msg.format(name=self.name, interval=_format_time(self.interval),
                         wall_interval=_format_time(self.wall_interval))

    def __str__(self):
        return self.msg

    def __repr__(self):
        if self.start is None:
            return "Timer(name={name})".format(**self.__dict__)
        msg = "Timer(name={name}, interval={interval},wall_interval={wall_interval})"
        return msg.format(**self.__dict__)


def fake_ohlc(N=1000, start="2000/01/01", freq="D"):
    """
        Meh, need to make this better behaved
    """
    ind = pd.date_range(start, freq=freq, periods=N)
    returns = (np.random.random(N) - .5) * .05
    geom = (1+returns).cumprod()

    open = 100 * geom
    close = open + (open * (np.random.random(N) - .5)) * .1
    high = np.maximum(open, close) + .01
    low = np.minimum(open, close) - .01
    vol = 10000 + np.random.random(N) * 10000

    df = pd.DataFrame(index=ind)
    df['open'] = open
    df['high'] = high
    df['low'] = low
    df['close'] = close
    df['vol'] = vol.astype(int)
    return df

def assert_columnpanel_equal(left, right):
    assert(isinstance(left, ColumnPanel))
    assert(isinstance(right, ColumnPanel))

    assert left.items == right.items
    assert left.index.equals(right.index)

    assert len(left.frames) == len(right.frames)

    for key, l_frame in left.frames.items():
        r_frame = right.frames[key]
        assert_frame_equal(l_frame, r_frame)

    test_col = left.columns[0]
    l_colframe = getattr(left, test_col)
    r_colframe = getattr(right, test_col)
    assert_frame_equal(l_colframe, r_colframe)

# grabbed from IPython/core/magics/execution.py
def _format_time(timespan, precision=3):
    """Formats the timespan in a human readable form"""
    import math

    if timespan >= 60.0:
        # we have more than a minute, format that in a human readable form
        # Idea from http://snipplr.com/view/5713/
        parts = [("d", 60*60*24),("h", 60*60),("min", 60), ("s", 1)]
        time = []
        leftover = timespan
        for suffix, length in parts:
            value = int(leftover / length)
            if value > 0:
                leftover = leftover % length
                time.append('%s%s' % (str(value), suffix))
            if leftover < 1:
                break
        return " ".join(time)


    # Unfortunately the unicode 'micro' symbol can cause problems in
    # certain terminals.
    # See bug: https://bugs.launchpad.net/ipython/+bug/348466
    # Try to prevent crashes by being more secure than it needs to
    units = ["s", "ms",'us',"ns"] # the save value
    if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
        try:
            '\xb5'.encode(sys.stdout.encoding)
            units = ["s", "ms",'\xb5s',"ns"]
        except:
            pass
    scaling = [1, 1e3, 1e6, 1e9]

    if timespan > 0.0:
        order = min(-int(math.floor(math.log10(timespan)) // 3), 3)
    else:
        order = 3
    ret =  "%.*g %s" % (precision, timespan * scaling[order], units[order])
    return ret

import unittest
import inspect

def setup_battery(targets, battery):
    """
        ind = pd.date_range(start="2000", freq="D", periods=10)
        targets = {}
        targets['int_series'] = lambda : pd.Series(range(10))
        targets['bool_series'] = lambda : pd.Series(np.random.randn(10) > 0, index=ind)
        targets['float_series'] = lambda : pd.Series(np.random.randn(10))
        targets['string_series'] = lambda : pd.Series(list('asdfqwerzx'), index=ind)

        class ShiftBattery(object):
            def test_check(self):
                obj = self._construct()
                if obj.is_time_series:
                    assert False, "Don't support time series"

        setup_battery(targets, ShiftBattery)
    """
    # global module scope of the calling function
    caller_globals = inspect.stack()[1][0].f_globals
    battery_name = battery.__name__
    # create a unittest.TestCase subclass for each target
    for target, maker in list(targets.items()):
        cls_name = "Test" + battery_name + '_' + target
        cls = makeClass(cls_name, battery, maker)
        caller_globals[cls_name] = cls

def makeClass(cls_name, battery, maker):
    cls = type(cls_name, (unittest.TestCase, battery), {})
    cls._construct = lambda self: maker()
    return cls
