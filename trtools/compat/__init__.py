try:
    import cPickle as pickle
    from itertools import izip
except ImportError:
    import pickle
    izip = zip
