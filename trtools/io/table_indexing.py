"""
    Stuff to make indexing/querying HDF5 faster
"""
import numpy as np

def create_slices(arr):
    """
        Take an array of index values and creates slices.

        DO NOT confuse this with a regular array of values. Indexing arr
        with a slice will not make sense. arr is an array of indexes to another
        array.

        arr = [1,2,5]
        s = create_slices(arr)
        arr[s[0]] != [1,2]
    """
    if arr.dtype == 'bool': # bool index array
        arr = np.nonzero(arr)[0]
    edges = np.nonzero(np.diff(arr) != 1)[0] + 1
    splits = np.split(arr, edges)
    slices = []
    for split in splits:
        slices.append(slice(split[0], split[-1]+1))
    return slices
