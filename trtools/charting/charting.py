import math
from itertools import izip

from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from pandas.util.decorators import Appender
from pandas import DataFrame, datetools, DatetimeIndex, Series, TimeSeries
from pandas.core.series import remove_na
from pandas.tseries.resample import _get_range_edges
from pandas.tseries.frequencies import to_offset, _is_annual, _is_weekly
import pandas.lib as lib
from matplotlib.finance import candlestick,\
             plot_day_summary 

import trtools.core.column_grep
from trtools.monkey import attr_namespace
from trtools.core.column_grep import *
import trtools.charting.styler as cstyler

import IPython

IN_NOTEBOOK = True
instance = IPython.Application._instance
if isinstance(instance, IPython.frontend.terminal.ipapp.TerminalIPythonApp):
    IN_NOTEBOOK = False

IPython.core.pylabtools.figsize(15, 10)

def figsize(width, height):
    IPython.core.pylabtools.figsize(width, height)

CURRENT_FIGURE = None

def reset_figure(*args):
    """
    In ipython notebook, clear the figure after each cell execute.
    This negates the need to specify a Figure for each plot
    """
    global CURRENT_FIGURE
    CURRENT_FIGURE = None

shell = IPython.InteractiveShell._instance
if IN_NOTEBOOK and shell:
    shell.register_post_execute(reset_figure)

class TimestampLocator(ticker.Locator):
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
        vmax = min(vmax, len(self.index) -1)

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

class TimestampFormatter(object):
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
        self._locator = TimestampLocator(self.index)
        ax.xaxis.set_major_locator(self._locator)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(self.format_date))
        ax.xaxis.grid(True)

def gcf(reset=False):
    global CURRENT_FIGURE
    if CURRENT_FIGURE is None or reset:
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
            self.init_ax(axnum, sharex, skip_na)
        self._set_ax(axnum)

    def align_xlim(self, axes=None):
        """
            Make sure the axes line up their xlims
        """
        # TODO take a param of ax numbers to align
        left = []
        right = []
        for grapher in self.graphers.values():
            if grapher.df is None:
                continue
            l, r = grapher.ax.get_xlim()
            left.append(l)
            right.append(r)

        for grapher in self.graphers.values():
            if grapher.df is None:
                continue
            grapher.ax.set_xlim(min(left), max(right)) 

    def plot(self, name, series, index=None, fillna=None, **kwargs):
        if self.ax is None:
            print('NO AX set')
            return
        self.figure.autofmt_xdate()
        self.grapher.plot(name, series, index, fillna, **kwargs)

    def boxplot(self, df, axis=0, *args, **kwargs):
        self.figure.autofmt_xdate()
        self.grapher.boxplot(df, axis=axis, *args, **kwargs)

    def candlestick(self, *args, **kwargs):
        if self.ax is None:
            print('NO AX set')
            return
        self.figure.autofmt_xdate()
        self.grapher.candlestick(*args, **kwargs)

    def ohlc(self, *args, **kwargs):
        if self.ax is None:
            print('NO AX set')
            return
        self.figure.autofmt_xdate()
        self.grapher.ohlc(*args, **kwargs)

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
        self.styler = cstyler.styler()
        self.yaxes = {}

    @property
    def right_ax(self):
        return self.yaxes.get('right', None)

    def is_datetime(self):
        return self.df.index.inferred_type in ('datetime', 'date', 'datetime64')

    def find_ax(self, secondary_y, kwargs):
        """
        multiple y-axis support. stay backward compatible with secondary_y
        
        Note: we take in the actual kwargs because we want to pop('yax')
        to affect the callers kwargs
        """
        yax = kwargs.pop('yax', None)
        if yax and secondary_y:
            raise Exception('yax and secondary_y should not both be set')
        if secondary_y:
            yax = 'right'

        ax = self.ax
        if yax:
            ax = self.get_yax(yax)
        return ax

    def plot(self, name, series, index=None, fillna=None, secondary_y=False, 
             **kwargs):

        # use default styler if one is not passed in
        styler = kwargs.pop('styler', self.styler)
        if styler:
            style_dict = next(styler)
            # note we do it this way so explicit args passed in kwargs
            # override style_dict
            kwargs = dict(style_dict.items() + kwargs.items())

        if self.sharex is not None:
            series = series.reindex(self.sharex.index, method=fillna)

        if self.df is None:
            self.df = DataFrame(index=series.index)
        
        is_datetime = self.is_datetime()
        if is_datetime:
            self.setup_datetime(self.df.index)

        # Previous we were using DataFrame.setitem to implicitly reindex
        # and then fillna later. This only works if the original series
        # has items that line up in the Grapher.df
        # We now reindex and fillna in one step. 
        # Ran into this when plotting daily data that had no normalized (midnight)
        # times. 
        if not np.isscalar(series):
            series = series.reindex(self.df.index, method=fillna)
        self.df[name] = series

        plot_series = self.df[name]

        if name is not None:
            kwargs['label'] = name

        xax = self.df[name].index
        if self.skip_na and is_datetime:
            xax = np.arange(len(self.df))
            self.formatter.index = self.df.index
        
        ax = self.find_ax(secondary_y, kwargs)
        ax.plot(xax, plot_series, **kwargs)

        # generate combined legend
        lines, labels = self.consolidate_legend()
        self.ax.legend(lines, labels, loc=0)

        if is_datetime: 
            # plot empty space for leading NaN and trailing NaN
            # not sure if I should only call this for is_datetime
            plt.xlim(0, len(self.df.index)-1)

    def consolidate_legend(self):
        """
        consolidate the legends from all axes and merge into one
        """
        lines, labels = self.ax.get_legend_handles_labels()
        for k, ax in self.yaxes.iteritems():
            new_lines, new_labels = ax.get_legend_handles_labels()
            lines = lines + new_lines
            labels = labels + new_labels
        return lines, labels

    def get_right_ax(self):
        return self.get_yax('right')

    def get_yax(self, name):
        """
        Get a yaxis keyed by name. Returns a newly
        generted twinx if it doesn't exist
        """
        def make_patch_spines_invisible(ax):
            ax.set_frame_on(True)
            ax.patch.set_visible(False)
            for sp in ax.spines.itervalues():
                sp.set_visible(False)

        size = len(self.yaxes)
        if name not in self.yaxes:
            ax = self.ax.twinx()
            self.yaxes[name] = ax
            # set spine 
            ax.spines["right"].set_position(("outward", 50 * size))    
            make_patch_spines_invisible(ax)
            ax.spines["right"].set_visible(True)
            ax.set_ylabel(name)

            self.set_formatter()
        return self.yaxes[name]

    def setup_datetime(self, index):
        """
            Setup the int based matplotlib x-index to translate
            to datetime

            Separated out here to share between plot and candlestick
        """
        is_datetime = self.is_datetime()
        if self.formatter is None and self.skip_na and is_datetime:
            self.formatter = TimestampFormatter(index)
            self.formatter.set_formatter(self.ax)

    def set_index(self, index):
        if self.df is not None:
            raise Exception("Cannot set index if df already exists")
        df = pd.DataFrame(index=index)
        self.df = df

    def boxplot(self, df, axis=0, secondary_y=False, *args, **kwargs):
        """
            Currently supports plotting DataFrames.

            Downside is that this only works for data that has equal columns. 
            For something like plotting groups with varying sizes, you'd
            need to use boxplot(list()). Example is creating a SeriesGroupBy.boxplot
        """
        if axis == 1:
            df = df.T
        index = df.columns 
        self.set_index(index)
        clean_values = [remove_na(x) for x in df.values.T]

        ax = self.find_ax(secondary_y, kwargs)

        # positions need to start at 0 to align with TimestampLocator
        ax.boxplot(clean_values, positions=np.arange(len(index)))
        self.setup_datetime(index)
        self.set_formatter()

    def boxplot_list(self, data, secondary_y=False, *args, **kwargs):
        pass

    def set_formatter(self):
        """ quick call to reset locator/formatter when lost. i.e. boxplot """
        if self.formatter:
            self.formatter.set_formatter(self.ax)

    def candlestick(self, index, open, high, low, close, width=0.3, secondary_y=False,
                   *args, **kwargs):
        """
            Takes a df and plots a candlestick. 
            Will auto search for proper columns
        """
        data = {}
        data['open'] = open
        data['high'] = high
        data['low'] = low
        data['close'] = close
        df = pd.DataFrame(data, index=index)
        self.add_data(df)

        # grab merged data
        xax = np.arange(len(self.df.index))
        quotes = izip(xax, self.df['open'], self.df['close'], self.df['high'], self.df['low'])

        ax = self.find_ax(secondary_y, kwargs)

        self.setup_datetime(index)
        candlestick(ax, quotes, width=width, colorup='g')

    def add_data(self, data):
        if self.df is None:
            self.df = data
        else: 
            # merge ohlc data
            for k,v in data.iterkv():
                self.df[k] = v

    def ohlc(self, df, width=0.3, *args, **kwargs):
        ohlc_df = normalize_ohlc(df)
        self.candlestick(df.index, ohlc_df.open, ohlc_df.high, ohlc_df.low, ohlc_df.close, *args, **kwargs)

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

    def plot_surface(self, df, *args, **kwargs):
        pass

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
    temp = series.astype(float).copy()
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

_fplot_doc = """
    Parameters
    ----------
    secondary_y : bool
        Plot on a secondary y-axis
"""
# Monkey Patches
@Appender(_fplot_doc)
def series_plot(self, label=None, *args, **kwargs):
    label = label or kwargs.get('label')
    label = label and label or self.name

    try:
        prefix = kwargs.pop('prefix')
        label = prefix +' '+label
    except:
        pass

    fig = gcf()
    fig.plot(str(label), self, *args, **kwargs)

Series.fplot = series_plot
TimeSeries.fplot = series_plot

def df_plot(self, *args, **kwargs):
    force_plot = kwargs.pop('force_plot', False)
    styler = kwargs.pop('styler', cstyler.marker_styler())

    if len(self.columns) > 20 and not force_plot:
        raise Exception("Are you crazy? Too many columns")

    # pass styler to each series plot
    kwargs['styler'] = styler
    for col in self.columns:
        series = self[col]
        series.fplot(*args, **kwargs)

DataFrame.fplot = df_plot

def series_plot_markers(self, label=None, *args, **kwargs):
    """
    Really just an automated way of calling gcf
    """
    label = label or kwargs.get('label')
    label = label and label or self.name
    fig = gcf()
    fig.plot_markers(str(label), self, *args, **kwargs)

Series.fplot_markers = series_plot_markers

def ohlc_plot(self, width=0.3, *args, **kwargs):
    fig = gcf()
    fig.ohlc(self, width=width, *args, **kwargs)

DataFrame.ohlc_plot = ohlc_plot

class PlotNS(object):
    pass

# take over .plot
@attr_namespace(Series, 'plot')
class SeriesPlotNS(PlotNS):
    @staticmethod
    def plot(self, *args, **kwargs):
        series_plot(*args, **kwargs)

@attr_namespace(DataFrame, 'plot')
class DataFramePlotNS(PlotNS):
    @staticmethod
    def plot(self, *args, **kwargs):
        df_plot(*args, **kwargs)

    @staticmethod
    def ohlc_plot(self, *args, **kwargs):
        ohlc_plot(*args, **kwargs)

# TODO SeriesByGroupBy.boxplot
"""
import matplotlib.ticker as ticker

labels = []
data = []
for label, group in grouped:
        labels.append(label)
            data.append(group)
r = labels
N = len(r)
ind = np.arange(N)  # the evenly spaced plot indices
def format_date(x, pos=None):
        thisind = np.clip(int(x+0.5), 0, N-1)
            return r[thisind].strftime('%Y-%m-%d')

        fig = gcf()
        ax = gca()
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        _ = boxplot(data) 
        fig.autofmt_xdate()
"""

