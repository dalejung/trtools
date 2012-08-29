def _filename(obj):
    try:
        return obj.__filename__()
    except:
        pass
    return str(obj)
