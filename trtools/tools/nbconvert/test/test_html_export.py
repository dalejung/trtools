from unittest import TestCase

import trtools.tools.nbconvert.html_export as he
from bs4 import BeautifulSoup

class TestHTMLExport(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_method(self):
        pass

"""
Tests I need to run:

    * Make sure that images are generating unique **STABLE** image filenames. Regardless of cells range
"""

if __name__ == '__main__':
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
