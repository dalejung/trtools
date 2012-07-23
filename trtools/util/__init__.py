import os

def open(name, mode='r', buffering=None):
    """
        Add special handling for passing in StringIO
    """
    return os.open(name, mode, buffering)
