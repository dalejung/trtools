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
import os.path

def bundle_filepath(path):
    filepath = os.path.abspath(path)
    filename = os.path.basename(path)
    filepath = os.path.join(filepath, filename)
    return filepath
