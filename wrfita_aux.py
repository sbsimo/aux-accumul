"""Define a class for reading WRF data"""
import os
import datetime

from netCDF4 import Dataset
import numpy as np
from osgeo import gdal, osr


class WrfItaAux:
    """A class used to read WRF data

    Attributes:
        abspath: str
            the absolute path to the file on disk in the os.path style
        dirname: str
            the absolute path to the parent directory containing the
            WRF file
        basename: str
            the filename of this WRF file
        period: datetime.timedelta
            the period of time this file refers to with respect to
            January 1st, 2000
        end_dt: datetime.datetime
            the instant in time corresponding to the end of the
            observation
        start_dt: datetime.datetime
            the instant in time corresponding to the start of the
            observation
        model_run_dt: datetime.datetime
            the instant in time corresponding to the run of the
            model
    """
    EPSG_CODE = 4326
    FILENAME_FORMAT = 'sft_rftm_rg_wrfita_aux_d02_%Y-%m-%d_00_*'

    def __init__(self, abspath):
        """
        :param abspath: str
            absolute path to the file on disk in the os.path style
        """
        self.abspath = abspath
        self.dirname, self.basename = os.path.split(abspath)
        with Dataset(abspath) as ds:
            self.period = datetime.timedelta(hours=ds.variables['time'][:][0])
        self.end_dt = datetime.datetime(2000, 1, 1) + self.period
        self.start_dt = self.end_dt - datetime.timedelta(hours=1)
        self.model_run_dt = datetime.datetime.strptime(self.basename[:-2], self.FILENAME_FORMAT[:-1])
        if self.model_run_dt > self.start_dt:
            self.start_dt = self.model_run_dt
        # geometric characteristics below
        self._x_min = None
        self._x_max = None
        self._y_min = None
        self._y_max = None
        self._pixel_size_x = None
        self._pixel_size_y = None
        self._geotransform = None
        # rain values below
        self._no_data_rainc = None
        self._no_data_rainnc = None
        self._no_data = None

    def __gt__(self, other):
        """Compare the current WrfItaAux object with another.

        Return true if the instant of initial time corresponding to the
        current object comes after the instant of initial time of the
        other object.

        :param other: WrfItaAux
            the other object in comparison
        :return: bool
        """
        return self.start_dt > other.start_dt

    def __lt__(self, other):
        """Compare the current WrfItaAux object with another.

        Return true if the instant of initial time corresponding to the
        other object comes after the instant of initial time of the
        current object.

        :param other: WrfItaAux
            the other object in comparison
        :return: bool
        """
        return self.start_dt < other.start_dt

    @property
    def x_min(self):
        """Get the minimum longitude value.

        :return: float
            A floating point number corresponding to the minimun
            longitude value
        """
        if self._x_min is None:
            self._x_min = self.lons[0]
        return self._x_min

    @property
    def x_max(self):
        """Get the maximum longitude value.

        :return: float
            A floating point number corresponding to the maximum
            longitude value
        """
        if self._x_max is None:
            self._x_max = self.lons[-1]
        return self._x_max

    @property
    def y_min(self):
        """Get the minimum latitude value.

        :return: float
            A floating point number corresponding to the minimun
            latitude value
        """
        if self._y_min is None:
            self._y_min = self.lats[0]
        return self._y_min

    @property
    def y_max(self):
        """Get the maximum latitude value.

        :return: float
            A floating point number corresponding to the maximum
            latitude value
        """
        # TODO produce tests for these
        if self._y_max is None:
            self._y_max = self.lats[-1]
        return self._y_max

    @property
    def pixel_size_x(self):
        """Get the pixel size along the longitude axis.

        :return: float
        """
        if self._pixel_size_x is None:
            self._pixel_size_x = (self.x_max - self.x_min)/(len(self.lons) - 1)
        return self._pixel_size_x

    @property
    def pixel_size_y(self):
        """Get the pixel size along the latitude axis.

        :return: float
        """
        # TODO implement test for these
        if self._pixel_size_y is None:
            self._pixel_size_y = (self.y_max - self.y_min)/(len(self.lats) - 1)
        return self._pixel_size_y

    @property
    def geotransform(self):
        """Get the affine geotransform coefficients.

        Generate the affine geotransform coefficients according to
        https://gdal.org/user/raster_data_model.html#affine-geotransform

        :return: tuple
            containing the six coefficients
        """
        if self._geotransform is None:
            self._geotransform = (self.x_min - self.pixel_size_x / 2, self.pixel_size_x, 0,
                                  self.y_min - self.pixel_size_y / 2, 0, self.pixel_size_y)
        return self._geotransform

    @property
    def rainc(self):
        """Get the array of RAINC values.

        Open the netCDF4 file on disk and read the RAINC variable, as
        well as the NoData value for it.

        :return: numpy.ndarray
        :raise: OSError
            in case the variable cannot be read.
        """
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
        """Get the array of RAINNC values.

        Open the netCDF4 file on disk and read the RAINNC variable, as
        well as the NoData value for it.

        :return: numpy.ndarray
        :raise: OSError
            in case the variable cannot be read.
        """
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
        """Get the total precipitation values.

        The total precipitation is calculated as the sum of the
        RAINC and RAINNC variables.

        :return: numpy.ndarray
        """
        return self.rainc + self.rainnc

    @property
    def lats(self):
        """Get the array of latitude values.

        Open the netCDF4 file on disk and read the lat variable.

        :return: numpy.ndarray
        :raise: OSError
            in case the variable cannot be read.
        """
        try:
            with Dataset(self.abspath) as ds:
                xs = ds.variables['lat'][:]
        except OSError as ose:
            print('Cannot read latitude data from: ', self.basename)
            raise ose
        return xs

    @property
    def lons(self):
        """Get the array of longitude values.

        Open the netCDF4 file on disk and read the lon variable.

        :return: numpy.ndarray
        :raise: OSError
            in case the variable cannot be read.
        """
        try:
            with Dataset(self.abspath) as ds:
                ys = ds.variables['lon'][:]
        except OSError as ose:
            print('Cannot read longitude data from: ', self.basename)
            raise ose
        return ys

    @property
    def no_data(self):
        """Get the NoData value from the netCDF original file.

        :return: float
        :raise: Value Error
            in case the NoData value for the RAINC and for the RAINNC
            differ from each other
        """
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
        """Write rain values to tiff.

        Generate a geotiff file with the sum of data contained in the
        RAINC and RAINNC variables

        :param: str
            the absolute path of the output file
            in the os.path flavour
        :return: int
            0 if successful
        """
        if not os.path.isabs(out_abspath):
            raise ValueError("The path provided is not absolute")
        if not isinstance(self.rain, np.ndarray):
            raise ValueError("The array provided is not a valid numpy array")
        gdal.AllRegister()
        driver = gdal.GetDriverByName('Gtiff')
        outDataset_options = ['COMPRESS=LZW']
        dtype = gdal.GDT_Float32
        outDataset = driver.Create(out_abspath, self.rain.shape[1], self.rain.shape[0], 1, dtype, outDataset_options)
        outDataset.SetGeoTransform(self.geotransform)
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
