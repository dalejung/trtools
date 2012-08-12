import pandas as pd

class Mismatcher(object):
    """
        Utility class to compare two DataFrames        
    """ 
    def __init__(self, old, new, primary_key):
        self.columns = old.columns.intersection(new.columns)
        self.mdf = pd.merge(old, new, on=primary_key, 
                            suffixes=('_old', '_new'), how='outer')
        self.primary_key = primary_key
        
    def diffs(self, col):
        s_new = self.mdf[col + '_new']
        s_old = self.mdf[col + '_old']
        mismatches = self.mdf[s_new != s_old]
        return mismatches.cols(self.primary_key, s_old.name, s_new.name)
    
    def __repr__(self):
        return repr(self.diffs())
    
    def __getattr__(self, key):
        if key in self.columns:
            return self.diffs(key)
        raise KeyError('Column not found') 
        
    def __getitem__(self, key):
        return self.mdf[self.mdf[self.primary_key] == key]
