import datetime

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
            self._build_serie()
        return self._serie

    @property
    def accumul(self):
        if self._accumul is None:
            self._accumul = np.around(np.sum(
                self.serie, axis=0, keepdims=False) / 2, 0).astype(np.int16)
        return self._accumul

    def _build_serie(self):
        for meas_fname in gpm_wrapper.get_gpms(self.datadir):
            meas_abspath = os.path.join(self.datadir, meas_fname)
            gpm_meas = gpm_wrapper.GPMImergeWrapper(meas_abspath)
            if gpm_meas.end_dt <= self.end_dt and \
                    gpm_meas.end_dt > self.start_dt:
                self.measurements.append(gpm_meas)
        if len(self.measurements) != self.exp_nmeas:
            raise ValueError("Missing measurements in the serie")
        self.measurements.sort(key=attrgetter('start_dt'))
        self.dt_index = tuple(measure.start_dt for measure in
                              self.measurements)
        self._serie = np.array([measure.precipCal for measure
                                in self.measurements])

    def save_accumul(self, out_abspath):
        array2tiff(self.accumul, out_abspath)

    def latest_subserie(self, duration):
        if self._serie is None:
            raise ValueError('No need to create a subserie from a'
                             ' non-built serie')

        if duration >= self.duration:
            raise ValueError('Required duration of subserie is greater '
                             'than original serie')

        subserie = PrecipTimeSerie(duration, self.end_dt, self.datadir)
        n_throw = self.exp_nmeas - subserie.exp_nmeas
        subserie.measurements = self.measurements[n_throw:]
        subserie.dt_index = self.dt_index[n_throw:]
        subserie._serie = self.serie[n_throw:]
        return subserie
