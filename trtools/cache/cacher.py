import collections
import functools
import cPickle as pickle
import os.path
import os

class cacher(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, filepath=None, method=False):
        self.func = None
        self.filepath = filepath
        self.method = method
        self.cache = {}
        self.first_run = False

    def check_dirs(self):
        dir, _ = os.path.split(self.filepath)
        if not os.path.exists(dir):
            print "Making dirs: %s" % dir
            os.makedirs(dir)

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            if self.filepath and not self.first_run:
                self.check_dirs()
                self.load()
                self.first_run = True

            if not isinstance(args, collections.Hashable):
                print 'not cacheable'
                # uncacheable. a list, for instance.
                # better to not cache than blow up.
                return func(*args)

            if self.method:
                key = hash(args[1:])
            else:
                key = hash(args)

            if key in self.cache:
                print 'return from cache'
                return self.cache[key]
            else:
                value = func(*args)
                self.cache[key] = value
                if self.filepath:
                    self.save()
                return value
        wrapper.cacher = self
        self.func = func
        return wrapper

    def save(self):
        with open(self.filepath, 'w') as f:
            pickle.dump(self.cache, f)

    def load(self):
        try:
            print 'Loading %s' % self.filepath
            with open(self.filepath) as f:
                self.cache = pickle.load(f)
        except IOError:
            print 'Cache file does not exist'

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)

    def clear(self):
        self.cache.clear()
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)

