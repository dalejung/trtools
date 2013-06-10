import io
import os

from IPython.nbformat import current as nbformat
from nbconvert.transformers import extractfigure
from nbconvert import FullHtmlExporter
from IPython.config import Config

def output_html_notebook(nb_path, asset_dir, start=None, end=None, filename=None, src_dir=''):
    """
    asset_dir : string
        Where to write out the image assets
    src_dir : string
        This is prepended to the image filename in <img src=""> tags. Separate from
        asset_dir since the webserving path might be different
    """
    if filename is None:
        filename = os.path.splitext(nb_path)[0]
        filename = os.path.split(filename)[1] + '.html'

    if src_dir is None:
        src_dir = asset_dir

    body, resources = process_html_notebook(nb_path, src_dir=src_dir, start=start, end=end)

    write_files(body, resources, filename, asset_dir)

def write_files(body, resources, filename, asset_dir):
    _write_main_file(body, filename)
    _write_assets(resources, asset_dir)

def _write_main_file(body, filename):
    # write html
    if not filename is None:
        with io.open(filename, 'w') as f:
            f.write(body)

def _write_assets(resources, asset_dir):
    #Get the key names used by the extract figure transformer
    figures_key = extractfigure.FIGURES_KEY
    binary_key = extractfigure.BINARY_KEY
    text_key = extractfigure.TEXT_KEY

    # write out images
    binkeys = resources.get(figures_key, {}).get(binary_key,{}).keys()
    textkeys = resources.get(figures_key, {}).get(text_key,{}).keys()
    if binkeys or textkeys :
        if not asset_dir is None:
            for key in binkeys:
                with io.open(os.path.join(asset_dir, key), 'wb') as f:
                    f.write(resources[figures_key][binary_key][key])
            #for key in textkeys:
            #    with io.open(os.path.join(asset_dir, key), 'w') as f:
            #        f.write(resources[figures_key][text_key][key])

c =  Config({
            'ExtractFigureTransformer':{'enabled':True}
            })

def process_html_notebook(nb_path, src_dir=None, start=None, end=None):

    with open(nb_path) as f:
        n = nbformat.read(f, 'ipynb')

    fullhtml = FullHtmlExporter(config=c)
    (nbc,resources) = fullhtml._preprocess(n, resources={})
    if src_dir:
        nbc = _prepend_srcdir(nbc, src_dir)
    # made the decision to have subset after image genration
    # the images are done via an iteration key. So we make sure to generate
    # the keys for the entire notebook and then grab the cells after wrds. 
    # this is to keep image names from clashing. image 33 will be image 33 regardless
    # of cells range
    nbc = _subset_cells(nbc, start, end)

    # render to html
    template = fullhtml.environment.get_template(fullhtml.template_file+fullhtml.template_extension)
    body = template.render(nb=nbc, resources=resources)
    return body, resources

def _subset_cells(nbc, start=None, end=None):
    """
    Modify notebook to only contain a range of cells

    Note: We only support one worksheet atm
    """
    worksheet = nbc.worksheets[0]
    cells = worksheet.cells[:]
    worksheet.cells = cells[start:end]
    return nbc

def _prepend_srcdir(nbc, src_dir, display_types=['png']):
    """
    Prepend src_dir to asset keys
    """
    display_keys = ['key_'+dt for dt in display_types]
    def _prepend_cell(cell):
        for out in cell.get('outputs', []):
            valid = [(dk, getattr(out, dk)) for dk in display_keys if hasattr(out, dk)]
            for dk, val in valid:
                out[dk] = os.path.join(src_dir, val)

    # prepend image directory to filenames
    for worksheet in nbc.worksheets:
        for cell in worksheet.cells:
            _prepend_cell(cell)

    return nbc
