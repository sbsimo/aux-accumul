import os
import configparser

import numpy as np
from osgeo import gdal, osr

from time_serie import PrecipTimeSerie


def tif2array(tif_abspath):
    ds = gdal.Open(tif_abspath, gdal.GA_ReadOnly)
    array = ds.GetRasterBand(1).ReadAsArray()
    return array


class AlertExtractor:
    # TIF_BASENAME = 'alerts_{:03d}h.tif'

    def __init__(self, serie, threshold):
        if not isinstance(serie, PrecipTimeSerie):
            raise ValueError('The serie object is not of type PrecipTimeSerie')
        self.serie = serie

        if not isinstance(threshold, Threshold):
            raise ValueError('The threshold object is not of type Threshold!')
        self.threshold = threshold

    @classmethod
    def from_serie(cls, serie_obj):
        threshold_obj = Threshold(int(serie_obj.duration.total_seconds() // 3600))
        return cls(serie_obj, threshold_obj)

    def get_alerts(self):
        return Alerts(self.serie.accumul > self.threshold.grid, self.serie.geotransform, self.serie.EPSG_CODE)

    def save_alerts(self, outdir):
        out_fname = 'gibbone_' + str(int(self.serie.duration.total_seconds() // 3600)) + 'h.tif'
        alerts_obj = self.get_alerts()
        alerts_obj.save2tiff(os.path.join(outdir, out_fname))

        # self.hours = int(serie.duration.total_seconds() // 3600)
        # try:
        #     self.threshold_obj = GridThreshold(self.hours)
        # except:
        #     print('Grid threshold not available for {:3d} hours duration'.format(self.hours))
        #     self.threshold_obj = Threshold(self.hours)

    # def get_masked_alerts(self):
    #     alerts = self.detect_alerts()
    #     mask = self.get_mask()
    #     return alerts * mask

    # def save_masked_alerts(self, out_dir):
    #     tif_basename = self.TIF_BASENAME.format(self.hours)
    #     tif_abspath = os.path.join(out_dir, tif_basename)
    #     array2tiff(self.get_masked_alerts(), tif_abspath)
    #
    # def get_mask(self):
    #     config = configparser.ConfigParser()
    #     config.read(THRESHOLDS_ABSPATH)
    #     mask_filename = config['Files']['mask']
    #     mask_dirname = os.path.dirname(THRESHOLDS_ABSPATH)
    #     mask_abspath = os.path.join(mask_dirname, mask_filename)
    #     gpm_mask = tiff2array(mask_abspath)
    #     return np.fliplr(gpm_mask.T)


class Threshold:
    def __init__(self, hours):
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
        if self._grid is None:
            self._grid = tif2array(self.tif_abspath)
            # grid_toflip = tif2array(self.tif_abspath).T
            # self._grid = np.fliplr(grid_toflip)
        return self._grid


class Alerts:
    def __init__(self, barray, geotransform, epsg_code):
        self.barray = barray
        self.geotransform = geotransform
        self.epsg_code = epsg_code
        self._mask = None
        self._masked_barray = None
        project_root = os.path.dirname(__file__)
        config_abspath = os.path.join(project_root, 'config.ini')
        config = configparser.ConfigParser()
        config.read(config_abspath)
        self.mask_fname = config['Mask filename']['mask']
        self.mask_abspath = os.path.join(project_root, 'tool_data', self.mask_fname)
        del config

    @property
    def mask(self):
        if self._mask is None:
            self._mask = tif2array(self.mask_abspath)
        return self._mask

    @property
    def masked_barray(self):
        if self._masked_barray is None:
            self._masked_barray = tif2array(self.mask_abspath) * self.mask
        return self._masked_barray

    def save2tiff(self, out_abspath):
        """Generate a geotiff file with the accumulated data

        :param out_abspath: a string containing the absolute path of the output file in the os.path flavour
        :return: 0 if successful
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
        print('alert file written!')
        return 0
