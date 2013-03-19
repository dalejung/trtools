"""
Idea is to turn on writing to images for all plots
"""
import os
import tempfile

import pandas as pd
import IPython
import IPython.core.pylabtools as pylabtools
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import trtools.charting.charting as charting

def save_to_pdf(file, figs=None):
    pp = PdfPages(file)

    if figs is None:
        figs = pylabtools.getfigs()

    for fig in figs:
        fig.savefig(pp, format='pdf')

    pp.close()
    close_figures()

def plot_pdf(fn=None, open=True):
    if fn is None:
        file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        fn = file.name
    save_to_pdf(fn)
    if open:
        os.system('open '+fn)
    return fn

def save_images(dir='', figs=None):
    if figs is None:
        figs = pylabtools.getfigs()

    for i, fig in enumerate(figs, 1):
        label = fig.get_label()
        if label == '':
            label = "Figure %d" % i
        fig.savefig(dir+label)

    close_figures()

def close_figures():
    plt.close('all')
    charting.gcf(reset=True)


# start of doing something where the execution stuff runs automatically?
def imagefile_reroute(func):
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapped

shell = IPython.InteractiveShell._instance
shell = None

# check so we don't break non ipython runs
if shell:
    execution_magic = shell.magics_manager.registry['ExecutionMagics']
    execution_magic.default_runner = imagefile_reroute(execution_magic.default_runner)
