from unittest import TestCase
import os.path

import trtools.tools.parallel

def curpath():
    pth, _ = os.path.split(os.path.abspath(__file__))
    return pth

class TestParallel(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_method(self):
        pass

if __name__ == '__main__':                                                                                          
    import nose                                                                      
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],exit=False)   
