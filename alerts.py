"""This module is needed for generating alerts.

Define a function for reading raster (geotiff) with one band from disk.
Also define three classes:
    - an AlertExtractor for generating the alerts
    - a Threshold class for reading and managing threshold values
    - an Alerts class for managing and saving alerts values
"""
import os
import configparser

import numpy as np
from osgeo import gdal, osr

from time_serie import PrecipTimeSerie


def tif2array(tif_abspath):
    """Read a geotiff file into an array

    :param tif_abspath: str
        the absolute path of the input file on disk
    :return: numpy.ndarray
        containing band 1 values
    """
    ds = gdal.Open(tif_abspath, gdal.GA_ReadOnly)
    array = ds.GetRasterBand(1).ReadAsArray()
    return array


class AlertExtractor:
    """A class needed for extracting alerts from a time serie,
    on the basis of alert values.

    Attributes:
        serie: PrecipTimeSerie
            a time series of precipitation data
        threshold: Threshold
            precipitation threshold values for the time series
    """
    def __init__(self, serie, threshold):
        """
        :param serie: PrecipTimeSerie
            a time series of precipitation data
        :param threshold: Threshold
            precipitation threshold values for the time series
        :raise ValueError
            if the arguments are not of appropriate types
        """
        if not isinstance(serie, PrecipTimeSerie):
            raise ValueError('The serie object is not of type PrecipTimeSerie')
        self.serie = serie

        if not isinstance(threshold, Threshold):
            raise ValueError('The threshold object is not of type Threshold!')
        self.threshold = threshold

    @classmethod
    def from_serie(cls, serie_obj):
        """Alternate constructor based on a serie instance only

        :param serie_obj: PrecipTimeSerie
        :return: AlertExtractor
        """
        threshold_obj = Threshold(int(serie_obj.duration.total_seconds() // 3600))
        return cls(serie_obj, threshold_obj)

    def get_alerts(self):
        """Generate and return an instance of Alert

        :return: Alert
        """
        return Alerts(self.serie.accumul > self.threshold.grid, self.serie.geotransform, self.serie.EPSG_CODE)

    def save_alerts(self, absfname):
        """Generate an instance of Alert and save its values to tiff

        :param absfname: str
            the absolute path of the output file on disk
        """
        alerts_obj = self.get_alerts()
        alerts_obj.save2tiff(absfname)


class Threshold:
    """A class for reading and managing threshold values

    Attributes:
        hours: int
            the duration of the accumulated precipitation
            to which the threshold values refer
        dirname: str
            the absolute path to the parent directory containing the
        tif_name: str
            the filename of the threshold raster on disk
        tif_abspath: str
            the absolute path of the threshold raster on disk
    """
    def __init__(self, hours):
        """
        :param hours: int
            the duration to which these threshold values refer
        :raise: ValueError
            if hours is not an int
        """
        if not isinstance(hours, int):
            raise ValueError('Duration must be expressed in hours, integer value is expected')
        self.hours = hours
        self._grid = None
        project_root = os.path.dirname(__file__)
        config_abspath = os.path.join(project_root, 'config.ini')
        config = configparser.ConfigParser()
        config.read(config_abspath)
        self.tif_name = config['Grid Thresholds'][str(hours) + 'h']
        self.tif_abspath = os.path.join(project_root, 'tool_data', self.tif_name)
        del config

    @property
    def grid(self):
        """Get the precipitation threshold-values in a grid

        :return: numpy.ndarray
        """
        if self._grid is None:
            self._grid = np.flipud(tif2array(self.tif_abspath))
        return self._grid


class Alerts:
    """A class to manage alerts data

        Attributes:
        barray: numpy.ndarray
            containing ones where alerts are
        geotransform: tuple
            containing the affine geotransform coefficients according to
            https://gdal.org/user/raster_data_model.html#affine-geotransform
        EPSG_CODE: int
            the code of the spatial reference
        mask_fname: str
            the filename for the sea/ocean mask
        mask_abspath: str
            the absolute path of the sea/ocean mask on disk
    """
    def __init__(self, barray, geotransform, epsg_code):
        """
        :param barray: numpy.ndarray
            containing ones where alerts are
        :param geotransform: tuple
            containing the affine geotransform coefficients according to
            https://gdal.org/user/raster_data_model.html#affine-geotransform
        :param epsg_code: int
            the code of the spatial reference
        """
        self.barray = barray
        self.geotransform = geotransform
        self.epsg_code = epsg_code
        self._mask = None
        self._masked_barray = None
        project_root = os.path.dirname(__file__)
        config_abspath = os.path.join(project_root, 'config.ini')
        config = configparser.ConfigParser()
        config.read(config_abspath)
        self.mask_fname = config['Filename formats']['mask']
        self.mask_abspath = os.path.join(project_root, 'tool_data', self.mask_fname)
        del config

    @property
    def mask(self):
        """Get the sea/ocean mask into an array

        :return: numpy.ndarray
        """
        if self._mask is None:
            self._mask = np.flipud(tif2array(self.mask_abspath))
        return self._mask

    @property
    def masked_barray(self):
        """Get the array of alerts with the mask applied.

        :return: numpy.ndarray
        """
        if self._masked_barray is None:
            self._masked_barray = self.barray * self.mask
        return self._masked_barray

    def save2tiff(self, out_abspath):
        """Write alert values to tiff.

        :param out_abspath: str
            the absolute path of the output file
            in the os.path flavour
        :return: int
            0 if successful
        """
        if not os.path.isabs(out_abspath):
            raise ValueError("The path provided is not absolute: " + out_abspath)
        if not isinstance(self.masked_barray, np.ndarray):
            raise ValueError("The array provided is not a valid numpy array")
        gdal.AllRegister()
        driver = gdal.GetDriverByName('Gtiff')
        outDataset_options = ['COMPRESS=LZW']
        dtype = gdal.GDT_Byte
        print('Writing alert file --> ', out_abspath)
        outDataset = driver.Create(out_abspath, self.masked_barray.shape[1], self.masked_barray.shape[0], 1,
                                   dtype, outDataset_options)
        outDataset.SetGeoTransform(self.geotransform)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(self.epsg_code)
        outDataset.SetProjection(srs.ExportToWkt())
        outband = outDataset.GetRasterBand(1)
        # TODO set no data?
        # nodata_value = np.iinfo(self.accumul.dtype).max
        # outband.SetNoDataValue(nodata_value)
        # self.accumul.fill_value = nodata_value
        outband.WriteArray(self.masked_barray)
        outband.GetStatistics(0, 1)
        del outband
        del outDataset
        print('\talert file written!')
        return 0
