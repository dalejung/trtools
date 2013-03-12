import itertools

import numpy as np
import pandas as pd

class MultiIndexGetter(object):
    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, name):
        if name in self.obj.names:
            return self.obj.get_level_values(name)
        raise AttributeError()
