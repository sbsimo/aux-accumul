import os
import configparser
import datetime

import pysftp

from wrfita_aux import WrfItaAux


class MirrorSFTP:
    def __init__(self):
        self.cnopts = pysftp.CnOpts()
        self.cnopts.hostkeys = None
        self.remote_folder = 'wrf'
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.HOST = config['SFTP']['HOST']
        self.USER = config['SFTP']['USER']
        self.PASSWORD = config['SFTP']['PASSWORD']
        self.DATADIR = os.path.join(os.path.dirname( __file__), config['STRUCTURE']['DATADIR'])

    def list_today_sftp_files(self):
        # TODO test this method
        sftp_files = self.list_sftp_files()
        file_prefix = datetime.date.today().strftime(WrfItaAux.FILENAME_FORMAT)[:-1]
        return [sftp_file for sftp_file in sftp_files if sftp_file.startswith(file_prefix)]

    def list_sftp_files(self):
        with pysftp.Connection(self.HOST, username=self.USER, password=self.PASSWORD, cnopts=self.cnopts) as sftp:
            filenames = sftp.listdir(self.remote_folder)
        return filenames

    def list_local_files(self):
        return os.listdir(self.DATADIR)

    def id_missing_files(self):
        sftp_file_names = set(self.list_today_sftp_files())
        local_file_names = set(self.list_local_files())
        return sftp_file_names - local_file_names

    def get_file(self, fname):
        remotepath = '/'.join([self.remote_folder, fname])
        localpath = os.path.join(self.DATADIR, fname)
        print('Saving {0} ...'.format(fname))
        for i in range(1, 4):
            print('    Attempt number ' + str(i))
            with pysftp.Connection(self.HOST, username=self.USER, password=self.PASSWORD, cnopts=self.cnopts) as sftp:
                sftp.get(remotepath, localpath)
            try:
                WrfItaAux(localpath)
                print('... done')
                return 0
            except Exception as exc:
                if os.path.exists(localpath):
                    try:
                        os.remove(localpath)
                    except Exception as int_exc:
                        print(int_exc.message)
                print('The download attempt number {:d} did not work, details below'.format(i))
                print(exc.message)
        return 1

    def get_files(self, fnames):
        for fname in fnames:
            self.get_file(fname)
        return 0

    def get_missing_files(self):
        self.get_files(self.id_missing_files())
        return 0

    def clean_workdir(self):
        local_fnames = set(self.list_local_files())
        relevant_fnames = set(self.list_today_sftp_files())
        to_be_deleted = local_fnames - relevant_fnames
        for fname in to_be_deleted:
            try:
                os.remove(os.path.join(self.DATADIR, fname))
                print('File removed: ', fname)
            except IsADirectoryError:
                try:
                    os.rmdir(os.path.join(self.DATADIR, fname))
                except:
                    print('Cannot remove ' + fname)
            except:
                print('Cannot remove' + fname)
