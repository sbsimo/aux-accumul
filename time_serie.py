import datetime

import numpy as np

class PrecipTimeSerie:
    """handle and manage a time serie of precipitation data"""

    def __init__(self, measures):
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

    @classmethod
    def latest(cls, duration, datadir):
        gpm_files = gpm_wrapper.get_gpms(datadir)
        gpm_files.sort()
        end_absfile = os.path.join(datadir, gpm_files[-1])
        end_gpmobj = gpm_wrapper.GPMImergeWrapper(end_absfile)
        end_dt = end_gpmobj.end_dt
        time_serie = cls(duration, end_dt, datadir)
        return time_serie

    @property
    def serie(self):
        if self._serie is None:
            self._serie = np.array([measure.rain for measure in self.measures])
        return self._serie

    @property
    def accumul(self):
        if self._accumul is None:
            self._accumul = np.around(np.sum(self.serie, axis=0, keepdims=False), 0).astype(np.int16)
        return self._accumul
