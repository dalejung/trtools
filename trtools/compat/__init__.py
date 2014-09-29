try:
    import cPickle as pickle
    from itertools import izip
    from StringIO import StringIO
    BytesIO = StringIO
except ImportError:
    from io import StringIO, BytesIO
    import pickle
    izip = zip
