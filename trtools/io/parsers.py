import numpy as np
import pandas as pd

def intdate_parse(dates):
    """
        Takes an array of in the form of
        19980101
        19980102
        19980103

        Returns a np.datetime64 array with M8[D] resolution
    """
    years = np.array(dates // 10000 - 1970, dtype='M8[Y]')
    days = dates % 100 - 1
    months = (dates % 10000) // 100 - 1
    dt = years.astype('M8[M]') + months
    dt = dt.values.astype('M8[D]') + days
    return dt

def add_times(dt, times, shift=None):
    """
        Takes a np.array(dtype='M8[D]') and adds a time array in form of
        930
        931
        932

        Returns a DatetimeIndex
        Takes a shift in minutes.
    """
    hours = times // 100
    total_minutes = hours * 60 + times % 100
    if shift:
        total_minutes += shift
    dt = dt.values.astype('M8[m]') + total_minutes.values
    dt = pd.DatetimeIndex(dt)
    return dt


def intdatetime_parse(dates, times, shift=None):
    """
        Takes an array of in the form of
        19980101
        19980102
    """
    dt = intdate_parse(dates)
    dt = add_times(dt, times, shift)
    return dt

# TODO Figure a generalized ohlc that returns a standard OHLC
def parse_ohlc(file, ticker):
    pass
