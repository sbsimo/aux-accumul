import os
import datetime

import numpy as np
from scipy.io import netcdf_file
from osgeo import gdal, osr


class Auxhist:
    """A class wrapper for aux data files"""

    def __init__(self, abspath):
        if not os.path.isfile(abspath):
            raise ValueError('This argument must be an absolute path to a netcdf file')
        self.abspath = abspath

        with netcdf_file(abspath) as nc:
            a = nc.variables['Times'].data.tostring()
            tokens = a.split(b'_')
            self.start_dt = datetime.datetime(*[int(token) for token in tokens[0].split(b'-')],
                                              *[int(token) for token in tokens[1].split(b':')])
        self.basename = os.path.basename(abspath)
        self.end_dt = self.start_dt + datetime.timedelta(hours=1)
        self._check_start_dt()

    def _check_start_dt(self):
        tokens = self.basename.split('_')
        date_tokens = [int(token) for token in tokens[2].split('-')]
        time_tokens = [int(token) for token in tokens[3:6]]
        declared_start_dt = datetime.datetime(*date_tokens, *time_tokens)
        delta_start_dt = declared_start_dt - self.start_dt
        if delta_start_dt > datetime.timedelta(minutes=1) or delta_start_dt < datetime.timedelta(minutes=-1):
            raise ValueError('The date and time declared in the filename are wrong!')

    @property
    def rainc(self):
        try:
            with netcdf_file(self.abspath) as nc:
                rainc = nc.variables['RAINC'].data[0].copy()
        except OSError as ose:
            print('Cannot read RAINC data from: ', self.basename)
            raise ose
        return rainc

    @property
    def rainnc(self):
        try:
            with netcdf_file(self.abspath) as nc:
                rainnc = nc.variables['RAINNC'].data[0].copy()
        except OSError as ose:
            print('Cannot read RAINC data from: ', self.basename)
            raise ose
        return rainnc

    @property
    def rain(self):
        return self.rainc + self.rainnc

    @property
    def lats(self):
        try:
            with netcdf_file(self.abspath) as nc:
                xs = nc.variables['XLAT'].data[0, :, 100].copy()
        except OSError as ose:
            print('Cannot read latitude data from: ', self.basename)
            raise ose
        return xs

    @property
    def lons(self):
        try:
            with netcdf_file(self.abspath) as nc:
                ys = nc.variables['XLONG'].data[0, 100, :].copy()
        except OSError as ose:
            print('Cannot read longitude data from: ', self.basename)
            raise ose
        return ys

    def __gt__(self, other):
        return self.start_dt > other.start_dt

    def __add__(self, other):
        return self.rain + other.rain

    def rain_to_tiff(self, out_abspath):
        if not os.path.isabs(out_abspath):
            raise ValueError("The path provided is not absolute")
        if not isinstance(self.rain, np.ndarray):
            raise ValueError("The array provided is not a valid numpy array")
        gdal.AllRegister()
        driver = gdal.GetDriverByName('Gtiff')
        geotransform = (-1215126.603, 11011.141, 0, 3470069.010, 0, 11011.138)
        outDataset_options = ['COMPRESS=LZW']
        dtype = gdal.GDT_Int16
        if self.rain.dtype == np.float32:
            dtype = gdal.GDT_Float32
        outDataset = driver.Create(out_abspath, self.rain.shape[1], self.rain.shape[0],
                                   1, dtype, outDataset_options)
        outDataset.SetGeoTransform(geotransform)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3857)
        outDataset.SetProjection(srs.ExportToWkt())
        outband = outDataset.GetRasterBand(1)
        outband.WriteArray(self.rain)
        outband.GetStatistics(0, 1)
        del outband
        del outDataset
