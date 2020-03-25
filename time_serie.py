import datetime
import glob
import os

import numpy as np

from auxdata import Auxhist

class PrecipTimeSerie:
    """handle and manage a time serie of precipitation data"""

    def __init__(self, measures):
        """Initialize a time serie object starting from an iterable of precipitation data

        :param measures: an iterable of Auxhist objects
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
        for absfname in glob.glob(os.path.join(datadir, 'auxhist*')):
            ah = Auxhist(absfname)
            if ah.start_dt < stop_dt and ah.end_dt > start_dt:
                measures.append(ah)
        if measures:
            return cls(measures)
        else:
            raise Exception('There are no suitable data in the folder, for the timeframe provided!')

    @classmethod
    def from_all_dir(cls, datadir):
        """Generate a time serie object given a folder

        :param datadir: a string representing a folder in the os.path flavour
        :return: a PrecipTimeSerie object
        """
        measures = [Auxhist(absfname) for absfname in glob.glob(os.path.join(datadir, 'auxhist*'))]
        if measures:
            return cls(measures)
        else:
            raise Exception('There are no suitable data in the folder, for the timeframe provided!')

    @classmethod
    def farthest(cls, datadir, duration):
        """Generate a time serie object given a folder and the ideal duration of the serie. This serie ends including
        the farthest data file in time available in the given folder

        :param datadir: a string representing a folder in the os.path flavour
        :param duration: a timedelta object representing the ideal duration of the serie
        :return: a PrecipTimeSerie object
        """
        file_list = glob.glob(os.path.join(datadir, 'auxhist*'))
        file_list.sort(reverse=True)
        stop_dt = datetime.datetime.strptime(file_list[0][-19:], Auxhist.DATE_FORMAT)
        start_dt = stop_dt - duration

        return cls.from_dir(datadir, start_dt, stop_dt)

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
            self._accumul = np.around(np.sum(self.serie, axis=0, keepdims=False), 0).astype(np.int16)
        return self._accumul
