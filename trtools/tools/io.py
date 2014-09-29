from trtools.compat import pickle

def save(obj, path_or_buffer):
    if isinstance(path_or_buffer, str):
        f = open(str, 'wb')
    else:
        f = path_or_buffer

    try:
        return pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    finally:
        f.close()

def load(path_or_buffer):
    if isinstance(path_or_buffer, str):
        f = open(str, 'rb')
    else:
        f = path_or_buffer

    try:
        return pickle.load(f)
    finally: 
        f.close()
