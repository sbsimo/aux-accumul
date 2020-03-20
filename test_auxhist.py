import unittest
import os
import random
import datetime

import numpy as np

from auxdata import Auxhist

DATADIR = os.path.join(os.path.dirname(__file__), 'auxfiles')


class TestAuxhist(unittest.TestCase):
    def setUp(self):
        fnames = os.listdir(DATADIR)
        fname = fnames[random.randrange(0, len(fnames))]
        abs_fname = os.path.join(DATADIR, fname)
        self.aux = Auxhist(abs_fname)

    def test_start_dt(self):
        self.assertIsInstance(self.aux.start_dt, datetime.datetime)

    def test_rain(self):
        self.assertIsInstance(self.aux.rain, np.ndarray)

    def test_rainnc(self):
        self.assertIsInstance(self.aux.rainnc, np.ndarray)

    def test_rainc(self):
        self.assertIsInstance(self.aux.rainc, np.ndarray)

    def tearDown(self) -> None:
        pass


if __name__ == '__main__':
    unittest.main()
