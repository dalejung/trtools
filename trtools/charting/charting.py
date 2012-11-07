import math
from itertools import izip

from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from pandas import DataFrame, datetools, DatetimeIndex, Series, TimeSeries
from pandas.tseries.resample import _get_range_edges
from pandas.tseries.frequencies import to_offset, _is_annual, _is_weekly
import pandas.lib as lib
from matplotlib.finance import candlestick,\
             plot_day_summary 

import trtools.core.column_grep
from trtools.core.column_grep import *

import IPython

IPython.core.pylabtools.figsize(15, 10)

def figsize(width, height):
    IPython.core.pylabtools.figsize(width, height)

CURRENT_FIGURE = None

class DateLocator(ticker.Locator):
    """  
    Place a tick on every multiple of some base number of points
    plotted, eg on every 5th point.  It is assumed that you are doing
    index plotting; ie the axis is 0, len(data).  This is mainly
    useful for x ticks.
    """
    def __init__(self, index, min_ticks=5):
        'place ticks on the i-th data points where (i-offset)%base==0'
        self.index = index
        self.min_ticks = min_ticks
        self.index_type = None

    def __call__(self):
        'Return the locations of the ticks'
        vmin, vmax = self.axis.get_view_interval() 
        xticks = self._process(vmin, vmax)
        return self.raise_if_exceeds(xticks)

    def _process(self, vmin, vmax):
        vmin = int(math.ceil(vmin))
        vmax = int(math.floor(vmax)) or len(self.index) - 1

        dmin = self.index[vmin] 
        dmax = self.index[vmax] 

        byIndex = self.infer_scale(dmin, dmax)
        self.index_type = byIndex

        sub_index = self.index[vmin:vmax]
        
        xticks = self.generate_xticks(sub_index, byIndex)
        return xticks

    def infer_scale(self, dmin, dmax):
        delta = datetools.relativedelta(dmax, dmin)

        numYears = (delta.years * 1.0) 
        numMonths = (numYears * 12.0) + delta.months
        numDays = (numMonths * 31.0) + delta.days
        numWeeks = numDays // 7
        numHours = (numDays * 24.0) + delta.hours
        numMinutes = (numHours * 60.0) + delta.minutes
        nums = [('AS', numYears), ('M', numMonths), ('W', numWeeks), ('D', numDays), ('H', numHours), 
                ('15min', numMinutes)] 
        byIndex = None
        for key, num in nums:
            if num > self.min_ticks:
                byIndex = key
                break

        return byIndex

    def generate_xticks(self, index, freq):
        """
            Ticks are really just the bin edges.
        """
        start = index[0]
        end = index[-1]
        start, end = _get_range_edges(index, offset=freq, closed='right')
        ind = DatetimeIndex(start=start, end=end, freq=freq)
        bins = lib.generate_bins_dt64(index.asi8, ind.asi8, closed='right')
        bins = np.unique(bins)
        return bins

class DateFormatter(object):
    def __init__(self, index):
        self.index = index
        self._locator = None

    def format_date(self, x, pos=None):
        thisind = np.clip(int(x+0.5), 0, len(self.index)-1)
        date = self.index[thisind]
        index_type = self._locator.index_type
        if index_type == 'T':
            return date.strftime('%H:%M %m/%d/%y')
        if index_type == 'H':
            return date.strftime('%H:%M %m/%d/%y')
        if index_type in ['D', 'W']:
            return date.strftime('%m/%d/%Y')
        if index_type == 'M':
            return date.strftime('%m/%d/%Y')
        return date.strftime('%m/%d/%Y %H:%M')

    def set_formatter(self, ax):
        self._locator = DateLocator(self.index)
        ax.xaxis.set_major_locator(self._locator)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(self.format_date))
        ax.xaxis.grid(True)

def gcf():
    global CURRENT_FIGURE
    if CURRENT_FIGURE is None:
        CURRENT_FIGURE = Figure(1)
    return CURRENT_FIGURE

def scf(figure):
    global CURRENT_FIGURE
    CURRENT_FIGURE = figure

class Figure(object):
    def __init__(self, rows=1, cols=1, skip_na=True):
        self.figure = plt.figure()
        self.rows = rows
        self.cols = cols
        self.ax = None
        self.axnum = None
        self.graphers = {}
        self.grapher = None
        self.skip_na = skip_na
        if rows == 1:
            self.set_ax(1)
        scf(self)

    def get_ax(self, axnum):
        if axnum not in self.graphers:
            return None
        return self.graphers[axnum].ax

    def _set_ax(self, axnum):
        self.axnum = axnum
        grapher = self.graphers[axnum]
        self.grapher = grapher
        self.ax = grapher.ax

    def init_ax(self, axnum, sharex=None, skip_na=None):
        if skip_na is None:
            skip_na = self.skip_na
        shared_df = None
        if type(sharex) == int:
            shared_df = self.graphers[sharex].df
        ax = plt.subplot(self.rows, self.cols, axnum)
        self.graphers[axnum] = Grapher(ax, skip_na, sharex=shared_df) 

    def set_ax(self, axnum, sharex=None, skip_na=None):
        if self.get_ax(axnum) is None:
            self.init_ax(axnum ,sharex, skip_na)
        self._set_ax(axnum)

    def plot(self, name, series, index=None, fillna=None, **kwargs):
        if self.ax is None:
            print('NO AX set')
            return
        self.figure.autofmt_xdate()
        self.grapher.plot(name, series, index, fillna, **kwargs)

    def candlestick(self, *args, **kwargs):
        if self.ax is None:
            print('NO AX set')
            return
        self.figure.autofmt_xdate()
        self.grapher.candlestick(*args, **kwargs)

    def plot_markers(self, name, series, yvalues=None, xindex=None, **kwargs):
        if self.ax is None:
            print('NO AX set')
            return
        self.grapher.plot_markers(name, series, yvalues, xindex, **kwargs)

    def clear(self, axnum=None):
        if axnum is None:
            axnum = self.axnum

        grapher = self.graphers[axnum]
        ax = grapher.ax
        ax.clear()
        del self.graphers[axnum]
        self.ax = None
        self.set_ax(axnum)

class Grapher(object):
    def __init__(self, ax, skip_na=True, sharex=None):
        self.df = None
        self.formatter = None
        self.ax = ax
        self.skip_na = skip_na
        self.sharex = sharex

    def is_datetime(self):
        return self.df.index.inferred_type in ('datetime', 'date', 'datetime64')

    def plot(self, name, series, index=None, fillna=None, **kwargs):
        if self.sharex is not None:
            series = series.reindex(self.sharex.index, method=fillna)

        if self.df is None:
            self.df = DataFrame(index=series.index)
        
        is_datetime = self.is_datetime()
        if is_datetime:
            self.setup_datetime(self.df.index)

        # we add to df to reindex
        # not sure how to handle if we start with a 
        # smaller index. i.e. hourly then trying to plot minute

        self.df[name] = series
        if name is not None:
            kwargs['label'] = name

        xax = self.df[name].index
        if self.skip_na and is_datetime:
            xax = np.arange(len(self.df))
            self.formatter.index = self.df.index
        
        plot_series = self.df[name]
        if fillna:
            plot_series = plot_series.fillna(method=fillna)
        self.ax.plot(xax, plot_series, **kwargs)
        plt.legend(loc=0)

    def setup_datetime(self, index):
        """
            Setup the int based matplotlib x-index to translate
            to datetime

            Separated out here to share between plot and candlestick
        """
        is_datetime = self.is_datetime()
        if self.formatter is None and self.skip_na and is_datetime:
            self.formatter = DateFormatter(index)
            self.formatter.set_formatter(self.ax)

    def candlestick(self, df, width=0.3):
        """
            Takes a df and plots a candlestick. 
            Will auto search for proper columns
        """
        xax = np.arange(len(df.index))
        ohlc_df = normalize_ohlc(df)
        quotes = izip(xax, ohlc_df.open, ohlc_df.close, ohlc_df.high, ohlc_df.low)
        ax = self.ax
        self.df = ohlc_df
        self.setup_datetime(ohlc_df.index)
        candlestick(ax, quotes, width=width, colorup='g')

    def plot_markers(self, name, series, yvalues=None, xindex=None, **kwargs):
        if yvalues is not None:
            series = process_signal(series, yvalues)
        props = {}
        props['linestyle'] = 'None'
        props['marker'] = 'o'
        props['markersize'] = 10
        props.update(kwargs)

        if xindex is not None:
            series = series.copy()
            series.index = xindex

        self.plot(name, series, **props)

def plot_markers(series, yvalues=None, xindex=None, **kwargs):
    if yvalues is not None:
        series = process_signal(series, yvalues)
    props = {}
    props['linestyle'] = 'None'
    props['marker'] = 'o'
    props['markersize'] = 10
    props.update(kwargs)

    index = series.index

    if xindex is not None:
        index = xindex

    plt.plot(index, series, **props)

def process_signal(series, source):
    """
        Take any non 0/na value and changes it to corresponding value of source
    """
    temp = series.copy()
    temp[temp == 0] = None
    temp *= source
    return temp

def remove_series(label, axes=None):
    """ Based on label name, remove a line """
    if axes is None:
        axes = plt.axes()
    for line in axes.lines:
        if line.get_label() == label:
            line.remove()

def clear_chart():
    lines = plt.axes().lines
    while True:
        try:
            lines.pop(0)
        except:
            break      
    plt.legend()

def remove_last_plot():
    lines = plt.axes().lines
    lines.pop(len(lines)-1)

# Monkey Patches
def series_plot(self, label=None, *args, **kwargs):
    label = label or kwargs.get('label')
    label = label and label or self.name
    try:
        prefix = kwargs.pop('prefix')
        label = prefix +' '+label
    except:
        pass
    fig = gcf()
    fig.plot(label, self, *args, **kwargs)

Series.fplot = series_plot
TimeSeries.fplot = series_plot

def df_plot(self, *args, **kwargs):
    if len(self.columns) > 20:
        print 'you crazy? too many columns'
        return;
    for col in self.columns:
        series = self[col]
        series.fplot(*args, **kwargs)

DataFrame.fplot = df_plot

def ohlc_plot(self, width=0.3, *args, **kwargs):
    fig = gcf()
    fig.candlestick(self)

DataFrame.ohlc_plot = ohlc_plot
