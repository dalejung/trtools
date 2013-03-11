_missing = object()

class cached_property(object):
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
        self.__module__ = func.__module__

    def __get__(self, inst, type=None):
        if inst is None:
            return self
        try:
            value = inst._prop_cache.get(self.__name__, _missing)
        except AttributeError:
            inst._prop_cache = {}
            value = _missing

        if value is _missing:
            value = self.func(inst)
            inst._prop_cache[self.__name__] = value
        return value
