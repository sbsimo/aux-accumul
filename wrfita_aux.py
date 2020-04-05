import os
import datetime

from netCDF4 import Dataset
import numpy as np
from osgeo import gdal, osr


class WrfItaAux:
    EPSG_CODE = 4326

    def __init__(self, abspath):
        self.abspath = abspath
        # TODO basename contains strange time format, check on manual
        self.dirname, self.basename = os.path.split(abspath)
        with Dataset(abspath) as ds:
            self.period = datetime.timedelta(hours=ds.variables['time'][:][0])
            self.start_dt = datetime.datetime(2000, 1, 1) + self.period
        self._no_data_rainc = None
        self._no_data_rainnc = None
        self._no_data = None

    def __gt__(self, other):
        return self.start_dt > other.start_dt

    @property
    def rainc(self):
        try:
            with Dataset(self.abspath) as ds:
                rainc = ds.variables['RAINC'][0]
                self._no_data_rainc = ds.variables['RAINC'][:].fill_value
        except OSError as ose:
            print('Cannot read RAINC data from: ', self.basename)
            raise ose
        return rainc

    @property
    def rainnc(self):
        try:
            with Dataset(self.abspath) as ds:
                rainnc = ds.variables['RAINNC'][0]
                self._no_data_rainnc = ds.variables['RAINNC'][:].fill_value
        except OSError as ose:
            print('Cannot read RAINNC data from: ', self.basename)
            raise ose
        return rainnc

    @property
    def rain(self):
        return self.rainc + self.rainnc

    @property
    def lats(self):
        try:
            with Dataset(self.abspath) as ds:
                xs = ds.variables['lat'][:]
        except OSError as ose:
            print('Cannot read latitude data from: ', self.basename)
            raise ose
        return xs

    @property
    def lons(self):
        try:
            with Dataset(self.abspath) as ds:
                ys = ds.variables['lon'][:]
        except OSError as ose:
            print('Cannot read longitude data from: ', self.basename)
            raise ose
        return ys

    @property
    def no_data(self):
        if self._no_data is None:
            if self._no_data_rainc is None:
                self.rainc
            if self._no_data_rainnc is None:
                self.rainnc
            if self._no_data_rainc != self._no_data_rainnc:
                raise ValueError("The NoData values for variables 'RAINC' and 'RAINNC' are different!")
            else:
                self._no_data = self._no_data_rainc
        return self._no_data

    def rain_to_tiff(self, out_abspath):
        """Generate a geotiff file with the sum of data contained in the RAINC and RAINNC variables

        :param out_abspath: a string containing the absolute path of the output file in the os.path flavour
        :return: 0 if successful
        """
        if not os.path.isabs(out_abspath):
            raise ValueError("The path provided is not absolute")
        if not isinstance(self.rain, np.ndarray):
            raise ValueError("The array provided is not a valid numpy array")
        gdal.AllRegister()
        driver = gdal.GetDriverByName('Gtiff')
        x_min = self.lons[0]
        x_max = self.lons[-1]
        x_gsd = (x_max - x_min)/(len(self.lons) - 1)
        y_min = self.lats[0]
        y_max = self.lats[-1]
        y_gsd = (y_max - y_min)/(len(self.lats) - 1)
        geotransform = (x_min, x_gsd, 0, y_min, 0, y_gsd)
        outDataset_options = ['COMPRESS=LZW']
        dtype = gdal.GDT_Float32
        outDataset = driver.Create(out_abspath, self.rain.shape[1], self.rain.shape[0],
                                   1, dtype, outDataset_options)
        outDataset.SetGeoTransform(geotransform)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(self.EPSG_CODE)
        outDataset.SetProjection(srs.ExportToWkt())
        outband = outDataset.GetRasterBand(1)
        outband.SetNoDataValue(-1.0)
        rain = self.rain
        rain.fill_value = -1.0
        outband.WriteArray(rain.filled())
        outband.GetStatistics(0, 1)
        del outband
        del outDataset
        return 0
