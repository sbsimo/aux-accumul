import unittest
import random
import os
import glob

from wrfita_aux import WrfItaAux

DATADIR = os.path.join(os.path.dirname(__file__), 'wrf')


class TestWrfItaData(unittest.TestCase):
    def setUp(self):
        abs_fnames = glob.glob(os.path.join(DATADIR, 'sft_rftm_rg_wrfita_aux_d02_*'))
        self.wrf = WrfItaAux(abs_fnames[random.randrange(0, len(abs_fnames))])

    def test_lats(self):
        self.assertEqual((447,), self.wrf.lats.shape)
        self.assertEqual(29.74, self.wrf.lats[0])
        self.assertEqual(59.800399999999996, self.wrf.lats[-1])

    def test_lons(self):
        self.assertEqual((764,), self.wrf.lons.shape)
        self.assertEqual(-10.92, self.wrf.lons[0])
        self.assertEqual(40.5062, self.wrf.lons[-1])

    def test_no_data(self):
        self.assertEqual(-8999999873090293122515668784119808, int(self.wrf.no_data))


if __name__ == '__main__':
    unittest.main()
