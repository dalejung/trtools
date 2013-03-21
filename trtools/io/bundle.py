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
import functools

import pandas as pd
from hdf5_store import HDFFile, OBTFile

def bundle_filepath(path):
    filepath = os.path.abspath(path)
    filename = os.path.basename(path)
    filepath = os.path.join(filepath, filename)
    return filepath

def _save_meta(obj, name, path):
    with open(os.path.join(path, name), 'wb') as f:
        pickle.dump(obj, f)

def _load_meta(name, path):
    with open(os.path.join(path, name), 'rb') as f:
        obj = pickle.load(f)
    return obj

def save_panel(panel, path, frame_key='frame_key'):
    """
    The bundle save_panel uses an OBTFile to store panels that have a large number of items. 
    Straight pickling these kind of panels is very slow. You could alternatively pickle each frame seprately
    and then recreate the Panel, but this makes IO fairly slow. 

    We use the OBTFile to make reading the entire block of data fast. We store the axis information
    in separate pickled files to support funky Indexes like ones made up of objects and multiple levels. 

    NOTE:
        The main constraint we're dealing with is that HDF doesn't like tables with columns
        sizes over 1000. By using OBT, we essentially remove the item axis and add one column (frame_key). 
        This means the column axis will be len(columns) + 1 which in most cases will be below 1000. 
        (You're more likely to have > 1000 simulation runs than have 1000 columns for each run). 

        In the future, it might be good to swapaxes based purely on which axis is smaller. i.e., maybe
        the columns and major_axis(dataframe.index) are too large but there are only 20 items. So we could store
        the panel where columns = (items) and rows = itertools.product(major_index, columns)

    Parameters
    ----------
    panel : Panel
    path : string
        Path to where the bundle dir will live. 
    frame_key : string
        If your item key is semantc and you plan on using the OBTFile on its own, it 
        could be useful to set this. If you don't plan on loading only subsets from
        disk and always load panels whole, using the default won't affect you.
    """
    filepath = bundle_filepath(path)
    store = OBTFile(filepath, 'w', frame_key=frame_key, type='directory')

    save_meta = functools.partial(_save_meta, path=path)
    # store extra metadata
    save_meta(panel.items, 'items')
    save_meta(panel.major_axis, 'index')
    save_meta(panel.minor_axis, 'columns')
    
    # TODO: I should reset frames to ordinal indexes and columns. 
    # This is so I don't have to trust pytabels/hdf5 with storing funky indexes
    # like object indexes. Would be easy enough to restore since I'm saving 
    # them via pickling
    # though in most cases, I have funky items (ParamSet objects for batch simulations) and not so much
    # in columns/index
    for i, item in enumerate(panel.items):
        frame = panel[item]
        store[i] = frame

def load_panel(path):
    """
    This portion is straight forward. Loads the data from save_panel and then sends it to 
    _panel which does the heavy lifting
    """
    filepath = bundle_filepath(path)
    store = OBTFile(filepath)
    #df = store.obt.table.read()
    df = store.obt.ix[:]

    load_meta = functools.partial(_load_meta, path=path)
    items = load_meta('items')
    index = load_meta('index')
    columns = load_meta('columns')

    panel = _panel(items, index, columns, df)
    return panel

def _panel(items, index, columns, df):
    """
    Parameters:
        items : Panel.items
        index : Panel.major_axis
        columns : Panel.columns
        df : pd.DataFrame
            data retrieved from OBTFile which are the Panel's item.values stakcked on top of each other 

    Note: 
        This only works if the data was stored in the HDF in order. The data is expected to be 
        np.ndarrays stacked up on top of each in order of the items list
    """
    vals = df.values
    # AH, I need to map out exactly why this works... I just know that it does
    vals = vals.reshape(len(items), len(columns) * len(index)) # (items) x (index x columns)
    df = pd.DataFrame(vals).T # (index x columns) * items
    df.columns = items
    new_index = list(itertools.product(index, columns))
    df.index = pd.MultiIndex.from_tuples(new_index)
    panel = df.to_panel()
    # to_panel ends up with reverse column order
    return panel.reindex(minor=columns)
