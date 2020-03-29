import unittest
import os
import glob
import datetime

import numpy as np

from time_serie import PrecipTimeSerie
from auxdata import Auxhist

DATADIR = os.path.join(os.path.dirname(__file__), 'auxfiles')
START_DT = datetime.datetime(2018, 7, 20, 1)
STOP_DT = datetime.datetime(2018, 7, 20, 11)


class TestTimeSerie(unittest.TestCase):
    def setUp(self):
        fpaths = glob.glob(os.path.join(DATADIR, 'aux*'))
        self.timeserie = PrecipTimeSerie([Auxhist(fpath) for fpath in fpaths])

    def test_serie(self):
        self.assertIsInstance(self.timeserie.serie, np.ndarray)

    def test_accumul(self):
        self.assertIsInstance(self.timeserie.accumul, np.ndarray)

    def test_accumul_to_tiff(self):
        #TODO: implement this test
        pass


class TestStartStopTimeSerie(unittest.TestCase):
    def setUp(self) -> None:
        self.timeserie = PrecipTimeSerie.from_dir(DATADIR, START_DT, STOP_DT)

    def test_number(self):
        self.assertEqual(10, len(self.timeserie))


class TestAllDataTimeSerie(unittest.TestCase):
    def setUp(self) -> None:
        self.timeserie = PrecipTimeSerie.from_all_dir(DATADIR)

    def test_number(self):
        self.assertEqual(12, len(self.timeserie))


class TestFarthestTimeSerie(unittest.TestCase):
    def setUp(self) -> None:
        self.duration = datetime.timedelta(hours=7)
        self.timeserie = PrecipTimeSerie.farthest(DATADIR, self.duration)

    def test_number(self):
        self.assertEqual(7, len(self.timeserie))

    def test_duration(self):
        self.assertEqual(self.duration, self.timeserie.duration)


if __name__ == '__main__':
    unittest.main()