from __future__ import division
import matplotlib.pyplot as plt
import numpy as np
from pylab import *

def _gen_labels(labels, names=None):
    if names is None:
        names = labels.names
    zips = [zip(names, l) for l in labels]
    new_labels = [', '.join(['{1}'.format(*m) for m in z]) for z in zips]
    return new_labels, names

def heatmap(data, xlabels=None, ylabels=None, title=None):
    fig, ax = plt.subplots()
    heatmap = ax.pcolormesh(data.values, cmap=plt.cm.RdYlGn)
    plt.colorbar(heatmap)


    xaxis = data.columns
    yaxis = data.index
    xlabels, xnames = _gen_labels(xaxis)
    ylabels, ynames = _gen_labels(yaxis)
    ax.set_xticklabels(xlabels, minor=False)
    ax.set_yticklabels(ylabels, minor=False)

    ax.set_xlabel(xnames)
    ax.set_ylabel(ynames)

    #yticks = np.arange(len(ylabels))

    # generate ticks at the first occurance of each new level 0
    labels, ind = np.unique(yaxis.labels[0], return_index=True)
    yticks = ind + 0.5

    ax.set_xticks(np.arange(len(xaxis))+0.5, minor=False)
    ax.set_yticks(yticks, minor=False)
    plt.xticks(rotation=90)
    ax.set_xlim(0, len(xaxis))
    ax.set_ylim(0, len(yaxis))
    if title:
        ax.set_title(title)
    return ax
