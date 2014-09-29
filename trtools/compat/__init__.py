try:
    import pickle as pickle
    from itertools import izip 
    from io import StringIO
    BytesIO = StringIO
except ImportError:
    from io import StringIO, BytesIO
    import pickle
    izip = zip
