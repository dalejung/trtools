from trtools.compat import pickle

def save(obj, path_or_buffer):
    if isinstance(path_or_buffer, basestring):
        f = open(basestring, 'wb')
    else:
        f = path_or_buffer

    try:
        return pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    finally:
        f.close()

def load(path_or_buffer):
    if isinstance(path_or_buffer, basestring):
        f = open(basestring, 'rb')
    else:
        f = path_or_buffer

    try:
        return pickle.load(f)
    finally: 
        f.close()
