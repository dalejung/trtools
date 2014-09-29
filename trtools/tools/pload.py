import trtools.tools.datapanel as datapanel
import multiprocessing

_store = None
def _load(key):
    return _store[key]

def pload(store, N=None, num_consumers=None):
    """
    Parallelize the reading of a mapping class. 

    This is useful for any IO abstraction where you want to read 
    many files at once

    Parameters:
        store : mapping object
        N : int
            number of items to process, mostly for debugging

    Note: This was built specifically for something like FileCache
    """
    # set global so consumers processes have access
    global _store
    _store = store

    keys = list(store.keys())

    if N is None:
        N = len(keys)

    results = {}
    # store on process so we aren't pickling it constantly
    pvars = {'store':store}
    loader = datapanel.DataPanel(keys, store=results)
    loader.process(_load, num=N, num_consumers=num_consumers, process_vars=pvars)
    return results
