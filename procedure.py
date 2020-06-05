import configparser
import os
import datetime

from time_serie import PrecipTimeSerie
from manage_ftp import MirrorSFTP
from alerts import AlertExtractor


def start(model_run_datetime=None):
    # build a serie
    # read working dir
    config = configparser.ConfigParser()
    config.read('config.ini')
    datadir = config['STRUCTURE']['DATADIR']
    # define duration
    duration_hours = (12, 24, 36, 48)
    for duration_hour in duration_hours:
        duration = datetime.timedelta(hours=duration_hour)
        # create obj
        tsobj = PrecipTimeSerie.earliest_from_dir(datadir, model_run_datetime, duration)
        # calculate accumulation --> no need to
        # write acculumation
        oabspath = os.path.join(datadir, 'outfile_accumul_{}_hours.tif'.format(duration_hour))
        tsobj.accumul_to_tiff(oabspath)
        # extract alerts and save
        AlertExtractor.from_serie(tsobj).save_alerts(datadir)


if __name__ == '__main__':
    # mirror_sftp_site()
    MirrorSFTP().get_missing_files()
    # for testing purposes fixing the model run date
    # model_run_datetime = datetime.datetime(2020, 4, 11)
    # start(model_run_datetime)
    start()
