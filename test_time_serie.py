import unittest
import os
import glob

from time_serie import PrecipTimeSerie
from auxdata import Auxhist

DATADIR = os.path.join(os.path.dirname(__file__), 'auxfiles')


class TestTimeSerie(unittest.TestCase):
    def setUp(self):
        fpaths = glob.glob(os.path.join(DATADIR, 'aux*'))
        self.timeserie = PrecipTimeSerie([Auxhist(fpath) for fpath in fpaths])

    def test_something(self):
        self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()