"""
    Eventually this is meant to flush out save/load functions that operate on directories instead of
    files. 

    Certain examples like pickling a directory of DataFrames are better handled by either picking each
    frame separately, or storing in an HDF5. 

    HDF5 itself has an issue when attaching large buckets of metadata. It makes more sense to keep the 
    HDF5 file relatively clean and put the meta data in whatever format(pickle) in the same directory. 

    In the future, there may be other examples where due to performance/features a single file
    persistance is undesirable. 
"""
import itertools
import os.path
import cPickle as pickle

import pandas as pd
from hdf5_store import HDFFile, OBTFile

def bundle_filepath(path):
    filepath = os.path.abspath(path)
    filename = os.path.basename(path)
    filepath = os.path.join(filepath, filename)
    return filepath

def save_panel(panel, path, frame_key):
    filepath = bundle_filepath(path)
    store = OBTFile(filepath, 'w', frame_key=frame_key, type='directory')
    items = panel.items
    index = panel.major_axis
    columns = panel.minor_axis

    with open(os.path.join(path, 'items'), 'wb') as f:
        pickle.dump(items, f)
    with open(os.path.join(path, 'index'), 'wb') as f:
        pickle.dump(index, f)
    with open(os.path.join(path, 'columns'), 'wb') as f:
        pickle.dump(columns, f)
    
    for i, item in enumerate(items):
        frame = panel[item]
        # helpful if key is an object
        store[i] = frame
    #frame = panel.to_frame(filter_observations=False)
    #index = frame.index
    #columns = frame.columns

def load_panel(path):
    filepath = bundle_filepath(path)
    store = OBTFile(filepath)
    #df = store.obt.table.read()
    df = store.obt.ix[:]

    with open(os.path.join(path, 'items'), 'rb') as f:
        items = pickle.load(f)
    with open(os.path.join(path, 'index'), 'rb') as f:
        index = pickle.load(f)
    with open(os.path.join(path, 'columns'), 'rb') as f:
        columns = pickle.load(f)

    panel = _panel(items, index, columns, df)
    return panel

def _panel(items, index, columns, df):
    vals = df.values
    vals = vals.reshape(len(items), len(columns) * len(index))
    df = pd.DataFrame(vals).T
    df.columns = items
    new_index = list(itertools.product(index, columns))
    df.index = pd.MultiIndex.from_tuples(new_index)
    panel = df.to_panel()
    # to_panel ends up with reverse column order
    return panel.reindex(minor=columns)
