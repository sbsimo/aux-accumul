import unittest
import os
import glob

import numpy as np

from time_serie import PrecipTimeSerie
from auxdata import Auxhist

DATADIR = os.path.join(os.path.dirname(__file__), 'auxfiles')


class TestTimeSerie(unittest.TestCase):
    def setUp(self):
        fpaths = glob.glob(os.path.join(DATADIR, 'aux*'))
        self.timeserie = PrecipTimeSerie([Auxhist(fpath) for fpath in fpaths])

    def test_serie(self):
        self.assertIsInstance(self.timeserie.serie, np.ndarray)

    def test_accumul(self):
        self.assertIsInstance(self.timeserie.accumul, np.ndarray)


if __name__ == '__main__':
    unittest.main()