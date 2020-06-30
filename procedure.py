import configparser
import os
import datetime
import json
import glob

from time_serie import PrecipTimeSerie
from manage_ftp import MirrorSFTP
from alerts import AlertExtractor

# read working dir and other congif from the configuration file
config = configparser.ConfigParser()
config.read('config.ini')
DATADIR = config['STRUCTURE']['DATADIR']
ACCUMUL_FNAME = config['Filename formats']['accumulated_rain']
ALERT_FNAME = config['Filename formats']['alert']
MODEL_RUN_REF_TIME = config['Filename formats']['model_run_ref_time']
del config
# define the absolute path on disk for the JSON file
# containing the latest run of the module
JSON_ABSFILEP = os.path.join(DATADIR, MODEL_RUN_REF_TIME)
# recall the format of the WRF filename
FILENAME_FORMAT = 'sft_rftm_rg_wrfita_aux_d02_%Y-%m-%d_00_*'


def start(model_run_datetime=None):
    """Perform the entire procedure for extracting the alerts.

    For the 24-hours and 48-hours periods:
    - extract the accumulated precipitation values and save it to disk
    - generate the alerts related to extreme precipitation
      and save them to disk

    The procedure run by default on the current date run,
    but can run for every model run date, if provided in input.

    :param model_run_datetime: datetime.datetime
        if provided, contains the date and time of the model run
    :return: None
    """
    # define duration for accumulation
    duration_hours = (24, 48)
    for duration_hour in duration_hours:
        duration = datetime.timedelta(hours=duration_hour)
        # create time serie instance
        tsobj = PrecipTimeSerie.earliest_from_dir(DATADIR, model_run_datetime, duration)
        # define the output absolute filename for the accumulated precipitation
        oabspath = os.path.join(DATADIR, ACCUMUL_FNAME.format(hours=duration_hour))
        # write the accumulated precipitation to disk
        tsobj.accumul_to_tiff(oabspath)
        # define the output absolute filename for the alerts file
        alert_absfname = os.path.join(DATADIR, ALERT_FNAME.format(hours=duration_hour))
        # extract alerts and save them to disk
        AlertExtractor.from_serie(tsobj).save_alerts(alert_absfname)
    # save model run timestamp
    with open(JSON_ABSFILEP, 'w') as jf:
        print('Writing json file with current model run datetime...')
        json.dump(tsobj.measures[0].model_run_dt.isoformat(), jf)
        print('\tjson file written!')


def clean_datadir():
    """Clean local working directory.

    In particular delete the files that are related to previous model runs.

    :return: None
    """
    with open(JSON_ABSFILEP, 'r') as jf:
        latest_model_run_dt = datetime.datetime.strptime(json.load(jf)[:11], '%Y-%m-%dT')
    to_keep = set(glob.glob(os.path.join(DATADIR, latest_model_run_dt.strftime(FILENAME_FORMAT))))
    all = set(glob.glob(os.path.join(DATADIR, FILENAME_FORMAT[:-13] + '*')))
    to_delete = all - to_keep
    print('Deleting ',  len(to_delete), ' older input files...')
    for absfname in to_delete:
        try:
            os.remove(absfname)
        except:
            print('Cannot remove file ', absfname, ' Please remove it manually.')
    print('\tfiles deleted!')


if __name__ == '__main__':
    # STEP 1 mirroring the sftp site,
    # by getting the files available for today
    MirrorSFTP().get_missing_files()
    # STEP 2 start the accumulation and alert calculation procedure
    start()
    # STEP 3 clean the local data directory from old files
    clean_datadir()

    ## ALTERNATIVELY
    ## for testing purposes you can impose the model run date, as done below.
    ## This allows to use old available data on disk, avoiding the download step.
    # model_run_dt = datetime.datetime(2020, 6, 5)
    ## Then start the process with that specific date
    # start(model_run_dt)
