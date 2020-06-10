import configparser
import os
import datetime
import json
import glob

from time_serie import PrecipTimeSerie
from manage_ftp import MirrorSFTP
from alerts import AlertExtractor

# read working dir
config = configparser.ConfigParser()
config.read('config.ini')
DATADIR = config['STRUCTURE']['DATADIR']
ACCUMUL_FNAME = config['Filename formats']['accumulated_rain']
ALERT_FNAME = config['Filename formats']['alert']
MODEL_RUN_REF_TIME = config['Filename formats']['model_run_ref_time']
del config
JSON_ABSFILEP = os.path.join(DATADIR, MODEL_RUN_REF_TIME)
FILENAME_FORMAT = 'sft_rftm_rg_wrfita_aux_d02_%Y-%m-%d_00_*'


def start(model_run_datetime=None):
    # build a serie
    # define duration
    duration_hours = (24, 48)
    for duration_hour in duration_hours:
        duration = datetime.timedelta(hours=duration_hour)
        # create obj
        tsobj = PrecipTimeSerie.earliest_from_dir(DATADIR, model_run_datetime, duration)
        # calculate accumulation --> no need to
        # write acculumation
        oabspath = os.path.join(DATADIR, ACCUMUL_FNAME.format(hours=duration_hour))
        tsobj.accumul_to_tiff(oabspath)
        # extract alerts and save
        alert_absfname = os.path.join(DATADIR, ALERT_FNAME.format(hours=duration_hour))
        AlertExtractor.from_serie(tsobj).save_alerts(alert_absfname)
    # save model run timestamp
    with open(JSON_ABSFILEP, 'w') as jf:
        print('Writing json file with current model run datetime...')
        json.dump(tsobj.measures[0].model_run_dt.isoformat(), jf)
        print('\tjson file written!')


def clean_datadir():
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
    # STEP 1 mirroring sftp site
    MirrorSFTP().get_missing_files()
    # STEP 2 start the alert calculation procedure
    start()
    # STEP 3 clean the input data directory from old files
    clean_datadir()

    # ALTERNATIVELY
    # for testing purposes you can fix the model run date, as done below
    # model_run_dt = datetime.datetime(2020, 6, 5)
    # start(model_run_dt)
