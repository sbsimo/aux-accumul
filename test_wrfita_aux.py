import unittest
import glob
import os
import random
import datetime

import numpy as np

from wrfita_aux import WrfItaAux

DATADIR = os.path.join(os.path.dirname(__file__), 'wrf')


class TestWrfItaAux(unittest.TestCase):
    def setUp(self):
        abs_fnames = glob.glob(os.path.join(DATADIR, 'sft_rftm_rg_wrfita_aux_d02_*'))
        self.wrf = WrfItaAux(abs_fnames[random.randrange(0, len(abs_fnames))])

    def test_start_dt(self):
        self.assertIsInstance(self.wrf.start_dt, datetime.datetime)

    def test_rain(self):
        self.assertIsInstance(self.wrf.rain, np.ndarray)
        self.assertEqual(2, self.wrf.rain.ndim)

    def test_rainnc(self):
        self.assertIsInstance(self.wrf.rainnc, np.ndarray)
        self.assertEqual(2, self.wrf.rain.ndim)

    def test_rainc(self):
        self.assertIsInstance(self.wrf.rainc, np.ndarray)
        self.assertEqual(2, self.wrf.rain.ndim)

    def test_lats(self):
        self.assertIsInstance(self.wrf.lats, np.ndarray)
        self.assertEqual(1, self.wrf.lats.ndim)

    def test_lons(self):
        self.assertIsInstance(self.wrf.lons, np.ndarray)
        self.assertEqual(1, self.wrf.lons.ndim)

    def test_no_data(self):
        self.assertIsInstance(self.wrf.no_data, np.float32)

    def test_rain_to_tiff(self):
        oabspath = os.path.join(self.wrf.dirname, 'geo' + self.wrf.basename + '.tif')
        self.assertEqual(0, self.wrf.rain_to_tiff(oabspath))
        if os.path.exists(oabspath):
            os.remove(oabspath)


if __name__ == '__main__':
    unittest.main()
