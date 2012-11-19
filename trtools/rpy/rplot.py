import tempfile
from glob import glob
from shutil import rmtree

import matplotlib
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import rpy2.robjects as robjects
r = robjects.r

from trtools.rpy.rmodule import get_func

def get_figsize():
    return matplotlib.rcParams['figure.figsize']

def get_dpi():
    return matplotlib.rcParams['figure.dpi']

class RPlot(object):
    def __init__(self):
        self.temp_dir = None

    def __enter__(self):
        self.start()

    def __exit__(self, type, value, traceback):
        self.end()

    def start(self):
        self.temp_dir = start()

    def end(self):
        process_plots(self.temp_dir)

def start(width=None, height=None, dpi=None):
    """
        Start writing R plots to temp_dir via png
    """
    if width is None or height is None:
        width, height = get_figsize()
    if dpi is None:
        dpi = get_dpi()

    temp_dir = tempfile.mkdtemp()
    filemask = "%s/Rplots%%03d.png" % (temp_dir)
    png(filemask, width=width, height=height, units='in', res=dpi)
    return temp_dir

def process_plots(temp_dir):
    """
        Take all rplots in temp_dir and plot them via matplotlib
    """
    r('dev.off()')

    images = [mpimg.imread(imgfile) for imgfile in glob("%s/Rplots*png" % temp_dir)]
    for image in images:
        plot_image(image)

    rmtree(temp_dir)

png = get_func('png')

def plot_image(image):
    """
        plot image data without a frame or axis
    """
    fig = plt.figure(frameon=False)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.imshow(image)
