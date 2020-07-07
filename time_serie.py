"""Define a class for generating and managing time serie data"""
import datetime
import glob
import os

import numpy as np
from osgeo import gdal, osr

from wrfita_aux import WrfItaAux

class PrecipTimeSerie:
    """Generate and manage a time serie of precipitation data

    Attributes:
        measures: list
            a list of observations of the WrfItaAux class
        start_dt: datetime.datetime
            the instant in which the time series begins
        stop_dt: datetime.datetime
            the instant in which the time series ends
        duration: datetime.timedelta
            the difference between the end and the start of the serie
        geotransform: tuple
            Generate the affine geotransform coefficients according to
            https://gdal.org/user/raster_data_model.html#affine-geotransform
        EPSG_CODE: int
            the code of the spatial reference
    """

    def __init__(self, measures):
        """
        :param measures: iterable of WrfItaAux objects
        """
        self.measures = list(measures)
        self.measures.sort()
        self.start_dt = self.measures[0].start_dt
        self.stop_dt = self.measures[-1].end_dt
        self.duration = self.stop_dt - self.start_dt

        for i in range(len(self.measures) - 1):
            deltat = self.measures[i + 1].start_dt - self.measures[i].end_dt
            if deltat > datetime.timedelta(minutes=1):
                raise ValueError('Some measurements are missing in the serie, in particular covering the time period '
                                 'following ' + self.measures[i].end_dt.isoformat())
        # geometric parameters
        self.geotransform = self.measures[0].geotransform
        self.EPSG_CODE = self.measures[0].EPSG_CODE

        self._serie = None
        self._accumul = None

    def __len__(self):
        """Get the number of measures in the serie.

        :return: int
        """
        return len(self.measures)

    @classmethod
    def from_dir(cls, datadir, start_dt, stop_dt):
        """An alternate constructor for the PrecipTimeSerie class.

        :param datadir: str
            a folder in the os.path flavour
        :param start_dt: datetime.datetime
            the ideal beginning of the serie
        :param stop_dt: datetime.datetime
            the ideal end of the serie
        :return: PrecipTimeSerie
        :raise: Exception
            in no WRF data is available in the folder
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
    def earliest_from_dir(cls, datadir, model_run_dt=None, duration=False):
        """Another alternate constructor for the PrecipTimeSerie class.

        Generate a time serie object given a folder and optionally
        the date of a model run and the duration of the serie.

        :param datadir: str
            a string representing a folder in the os.path flavour
        :param model_run_dt: datetime.datetime
            a datetime object representing the model run date and time
            (default is the current day at midnight)
        :param duration: datetime.timedelta
            the duration of the time serie (default is undefined)
        :return: PrecipTimeSerie
        :raise: ValueError
            in case the model_run_dt or the duration params don't have
            an appropriate type
        """
        measures = [WrfItaAux(absfname) for absfname in glob.glob(os.path.join(datadir,
                                                                               'sft_rftm_rg_wrfita_aux_d02_*'))]

        if model_run_dt is None:
            model_run_dt = datetime.datetime.combine(datetime.date.today(), datetime.time())
        else:
            if not isinstance(model_run_dt, datetime.datetime):
                raise ValueError
        filtered_measures = []
        for measure in measures:
            if measure.model_run_dt == model_run_dt:
                filtered_measures.append(measure)

        if duration:
            if not isinstance(duration, datetime.timedelta):
                raise ValueError
            refiltered_measures = []
            for measure in filtered_measures:
                if measure.start_dt < model_run_dt + duration:
                    refiltered_measures.append(measure)
        else:
            refiltered_measures = filtered_measures

        if refiltered_measures:
            tsobj = cls(refiltered_measures)
            if duration and duration > tsobj.duration:
                raise Exception('Missing measures in the serie, the period is not complete!')
            return tsobj
        else:
            raise Exception('There are no suitable data in the folder, for the timeframe provided!')

    @property
    def serie(self):
        """Get the precipitation time serie.

        Generates and returns a 3d array with the precipitation data
        for the entire time serie.

        :return: numpy.ndarray
        """
        if self._serie is None:
            self._serie = np.array([measure.rain for measure in self.measures])
        return self._serie

    @property
    def accumul(self):
        """Get the accumulated precipitation.

        Generates and returns a 2d array with the accumulated
        precipitation data for the entire time serie.

        :return: numpy.ndarray
        """
        if self._accumul is None:
            self._accumul = self.measures[-1].rain.astype(np.int16)
        return self._accumul

    def accumul_to_tiff(self, out_abspath):
        """Write accumulated rain values to geotiff.

        :param: str
            the absolute path of the output file
            in the os.path flavour
        :return: int
            0 if successful
        """
        if not os.path.isabs(out_abspath):
            raise ValueError("The path provided is not absolute: " + out_abspath)
        if not isinstance(self.accumul, np.ndarray):
            raise ValueError("The array provided is not a valid numpy array")
        gdal.AllRegister()
        driver = gdal.GetDriverByName('Gtiff')
        outDataset_options = ['COMPRESS=LZW']
        dtype = gdal.GDT_Int16
        print('Writing accumulation file --> ', out_abspath)
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
        print('\taccumulation file written!')
        del outband
        del outDataset
        return 0
