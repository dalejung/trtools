import pandas as pd
import time
import datetime

DATAIMPORT_ENABLED = True
#DATAIMPORT_CACHE_KEY = 'test_data_blah'
DATAIMPORT_VARS = [123, '111', True, 1.0]

def bob():
    time.sleep(3)
    whee = '123'
    return whee

v1 = 1
v2 = 2
v3 = 3
v4 = 4
v5 = 5
v6 = 6

b = bob()

df = pd.util.testing.makeDataFrame()

dale = 'dale'
ddd = 'ddd'
dd = datetime.datetime.now()

wooooo = 'woo'
