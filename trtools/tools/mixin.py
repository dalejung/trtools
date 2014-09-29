# http://c2.com/cgi/wiki?MixinsForPython
def mixIn (base, addition):
    """Mixes in place, i.e. the base class is modified.
    Tags the class with a list of names of mixed members.
    """
    assert not hasattr(base, '_mixed_')
    mixed = []
    for item, val in list(addition.__dict__.items()):
        if not hasattr(base, item):
            setattr(base, item, val)
            mixed.append (item)
    base._mixed_ = mixed
