class attrdict(dict):
    """A dict whose items can also be accessed as member variables.

    >>> d = attrdict(a=1, b=2)
    >>> d['c'] = 3
    >>> print d.a, d.b, d.c
    1 2 3
    >>> d.b = 10
    >>> print d['b']
    10

    # but be careful, it's easy to hide methods
    >>> print d.get('c')
    3
    >>> d['get'] = 4
    >>> print d.get('a')
    Traceback (most recent call last):
    TypeError: 'int' object is not callable
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self

    def __getattr__(self, name):
        try:
             return self[name]
        except:
            raise AttributeError()

    def __getitem__(self, name):
        """
            A regular key in dict will match on hash. 

            This version matches on __eq__ if the hash doesn't match.

            # NOTE: This can possibly lead to both perf hits and situations
            # where two keys match the same other. 
        """
        # regular ole dict check
        if name in self.__dict__:
            return dict.__getitem__(self, name)

        # list.__contains__ uses eq() to check membership
        keys = self.keys()
        if name in keys:
            ind = keys.index(name)
            return self[keys[ind]]
        raise KeyError()
