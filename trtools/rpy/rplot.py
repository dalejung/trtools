import tempfile
from glob import glob
from shutil import rmtree

import matplotlib
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import rpy2.robjects as robjects
r = robjects.r

IN_NOTEBOOK = True
import IPython
instance = IPython.Application._instance
# IPython.frontend was flattened so its submodule now live in the root
# namespace. i.e. IPython.frontend.terminal -> IPython.terminal
if hasattr(IPython, 'frontend'):
    terminal = IPython.frontend.terminal.ipapp.TerminalIPythonApp
else:
    terminal = IPython.terminal.ipapp.TerminalIPythonApp

if isinstance(instance, terminal):
    IN_NOTEBOOK = False

RPLOT_CONTEXT = None

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

png = r['png']

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
    png(filemask, width=width, height=height, units='in', res=dpi, pointsize=34)
    return temp_dir

def process_plots(temp_dir):
    """
        Take all rplots in temp_dir and plot them via matplotlib
    """
    r('dev.off()')

    images = [mpimg.imread(imgfile) for imgfile in glob("%s/Rplots*png" % temp_dir)]
    for image in images:
        plot_image(image)

    if images:
        print 'RPlot processed {count} images'.format(count=len(images))
    plt.show()
    rmtree(temp_dir)

def plot_image(image):
    """
        plot image data without a frame or axis
    """
    fig = plt.figure(frameon=False)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.imshow(image)

def wrapped_call(self, *args, **kwargs):
    """
        Wraps around Function.__call__ to enable
        RPlotting.
        #TODO There has to be a better way to do this.
    """
    global RPLOT_CONTEXT
    # within context short-circuit
    if RPLOT_CONTEXT is not None:
        res = self.__base_call__(*args, **kwargs)
        return res

    if RPLOT_CONTEXT is None:
        RPLOT_CONTEXT = RPlot()
        RPLOT_CONTEXT.start()

    res = self.__base_call__(*args, **kwargs)

    if RPLOT_CONTEXT is not None:
        RPLOT_CONTEXT.end()
        RPLOT_CONTEXT = None
    return res

def patch_call():
    """
        Wrap around the Function call to enable rplot -> matplotlib
    """
    if hasattr(robjects.Function, '__base_call__'):
        return
    robjects.Function.__base_call__ = robjects.Function.__call__
    robjects.Function.__call__ = wrapped_call
