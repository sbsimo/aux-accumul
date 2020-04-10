import datetime
import glob
import os

import numpy as np
from osgeo import gdal, osr

from wrfita_aux import WrfItaAux

class PrecipTimeSerie:
    # TODO change the docs
    """handle and manage a time serie of precipitation data"""

    def __init__(self, measures):
        """Initialize a time serie object starting from an iterable of precipitation data

        :param measures: an iterable of WrfItaAux objects
        """
        self.measures = measures
        self.measures.sort()
        self.start_dt = self.measures[0].start_dt
        self.stop_dt = self.measures[-1].end_dt
        self.duration = self.stop_dt - self.start_dt

        for i in range(len(self.measures) - 1):
            deltat = self.measures[i + 1].start_dt - self.measures[i].end_dt
            if deltat > datetime.timedelta(minutes=1):
                raise ValueError('Some measurements are missing in the serie')
        # geometric parameters
        self.geotransform = self.measures[0].geotransform
        self.EPSG_CODE = self.measures[0].EPSG_CODE

        self._serie = None
        self._accumul = None

    def __len__(self):
        return len(self.measures)

    @classmethod
    def from_dir(cls, datadir, start_dt, stop_dt):
        """Generate a time serie object given a folder and a start and a stop datetime

        :param datadir: a string representing a folder in the os.path flavour
        :param start_dt: a datetime representing the ideal beginning of the serie
        :param stop_dt: a datetime representing the ideal end of the serie
        :return: a PrecipTimeSerie object
        """
        measures = []
        for absfname in glob.glob(os.path.join(datadir, 'sft_rftm_rg_wrfita_aux_d02_*')):
            ah = WrfItaAux(absfname)
            if ah.start_dt < stop_dt and ah.end_dt > start_dt:
                measures.append(ah)
        if measures:
            return cls(measures)
        else:
            raise Exception('There are no suitable data in the folder, for the timeframe provided!')

    @classmethod
    def from_all_dir(cls, datadir, model_run_dt=False):
        """Generate a time serie object given a folder and the date of a model run.

        :param datadir: a string representing a folder in the os.path flavour
        :param model_run_dt: a datetime object representing the model run date and time (default is the current day
         at midnight)
        :return: a PrecipTimeSerie object
        """
        if not model_run_dt:
            model_run_dt = datetime.datetime.combine(datetime.date.today(), datetime.time())
        measures = [WrfItaAux(absfname) for absfname in glob.glob(os.path.join(datadir,
                                                                               'sft_rftm_rg_wrfita_aux_d02_*'))]
        filtered_measures = []
        for measure in measures:
            if measure.model_run_dt == model_run_dt:
                filtered_measures.append(measure)

        if filtered_measures:
            return cls(filtered_measures)
        else:
            raise Exception('There are no suitable data in the folder, for the timeframe provided!')

    @property
    def serie(self):
        """Generates and returns a 3d array with the precipitation data for the entire time serie

        :return: a 3d numpy array
        """
        if self._serie is None:
            self._serie = np.array([measure.rain for measure in self.measures])
        return self._serie

    @property
    def accumul(self):
        """Generates and returns a 2d array with the accumulated precipitation data for the entire time serie"""
        if self._accumul is None:
            self._accumul = self.measures[-1].rain.astype(np.int16)
        return self._accumul

    def accumul_to_tiff(self, out_abspath):
        """Generate a geotiff file with the accumulated data

        :param out_abspath: a string containing the absolute path of the output file in the os.path flavour
        :return: 0 if successful
        """
        if not os.path.isabs(out_abspath):
            raise ValueError("The path provided is not absolute")
        if not isinstance(self.accumul, np.ndarray):
            raise ValueError("The array provided is not a valid numpy array")
        gdal.AllRegister()
        driver = gdal.GetDriverByName('Gtiff')
        outDataset_options = ['COMPRESS=LZW']
        dtype = gdal.GDT_Int16
        outDataset = driver.Create(out_abspath, self.accumul.shape[1], self.accumul.shape[0], 1,
                                   dtype, outDataset_options)
        outDataset.SetGeoTransform(self.geotransform)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(self.EPSG_CODE)
        outDataset.SetProjection(srs.ExportToWkt())
        outband = outDataset.GetRasterBand(1)
        nodata_value = np.iinfo(self.accumul.dtype).max
        outband.SetNoDataValue(nodata_value)
        self.accumul.fill_value = nodata_value
        outband.WriteArray(self.accumul.filled())
        outband.GetStatistics(0, 1)
        del outband
        del outDataset
        return 0
