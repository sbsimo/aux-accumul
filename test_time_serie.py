import unittest
import os
import glob
import datetime

import numpy as np

from time_serie import PrecipTimeSerie
from wrfita_aux import WrfItaAux

DATADIR = os.path.join(os.path.dirname(__file__), 'wrf')
START_DT = datetime.datetime(2020, 4, 1, 2)
STOP_DT = datetime.datetime(2020, 4, 1, 10)


class TestTimeSerie(unittest.TestCase):
    def setUp(self):
        fpaths = glob.glob(os.path.join(DATADIR, 'sft_rftm_rg_wrfita_aux_d02_*'))
        self.timeserie = PrecipTimeSerie([WrfItaAux(fpath) for fpath in fpaths])

    def test_serie(self):
        self.assertIsInstance(self.timeserie.serie, np.ndarray)
        self.assertEqual(3, self.timeserie.serie.ndim)

    def test_accumul(self):
        self.assertIsInstance(self.timeserie.accumul, np.ndarray)
        self.assertEqual(2, self.timeserie.accumul.ndim)

    def test_accumul_to_tiff(self):
        oabspath = os.path.join(DATADIR, 'geo' + str(self.timeserie.duration.seconds // 3600) + '.tif')
        self.assertEqual(0, self.timeserie.accumul_to_tiff(oabspath))
        if os.path.exists(oabspath):
            os.remove(oabspath)


class TestStartStopTimeSerie(unittest.TestCase):
    def setUp(self) -> None:
        self.timeserie = PrecipTimeSerie.from_dir(DATADIR, START_DT, STOP_DT)

    def test_number(self):
        self.assertEqual(9, len(self.timeserie))


class TestAllDataTimeSerie(unittest.TestCase):
    def setUp(self) -> None:
        self.timeserie = PrecipTimeSerie.earliest_from_dir(DATADIR)

    def test_number(self):
        self.assertEqual(11, len(self.timeserie))


if __name__ == '__main__':
    unittest.main()
