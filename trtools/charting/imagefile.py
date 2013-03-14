import IPython
import pandas as pd
import matplotlib.pylab as pylab
import matplotlib.pyplot as pyplot
import trtools.charting.api as charting

import IPython.core.pylabtools as pylabtools


s = pd.Series(range(10))

fig = charting.Figure(1)
s.fplot()
fig = charting.Figure(1)
s.fplot()

figs = pylabtools.getfigs()

DIR = ''
for i, fig in enumerate(figs, 1):
    label = fig.get_label()
    if label == '':
        label = "Figure %d" % i
    fig.savefig(DIR+label)
