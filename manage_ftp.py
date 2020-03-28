import os
import configparser

import pysftp

from auxdata import Auxhist

DATADIR = os.path.join(os.path.dirname(__file__), 'data', 'auxfiles')


class AuxSFTP:

    def __init__(self):
        self.cnopts = pysftp.CnOpts()
        self.cnopts.hostkeys = None
        self.remote_folder = 'auxfiles'
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.HOST = config['SFTP']['HOST']
        self.USER = config['SFTP']['USER']
        self.PASSWORD = config['SFTP']['PASSWORD']

    def list_sftp_files(self):
        with pysftp.Connection(self.HOST, username=self.USER, password=self.PASSWORD, cnopts=self.cnopts) as sftp:
            filenames = sftp.listdir(self.remote_folder)
        return filenames

    def list_local_files(self):
        return os.listdir(DATADIR)

    def id_missing_files(self):
        sftp_file_names = set(self.list_sftp_files())
        local_file_names = set(self.list_local_files())

        files_conversion = {sftp_fname.replace(':', '_'): sftp_fname for sftp_fname in sftp_file_names}
        missing_clean_fnames = set(files_conversion.keys()) - local_file_names

        return [v for k, v in files_conversion.items() if k in missing_clean_fnames]

    def get_file(self, fname):
        clean_fname = fname.replace(':', '_')
        remotepath = '/'.join([self.remote_folder, fname])
        localpath = os.path.join(DATADIR, clean_fname)
        print('Saving {0}\n    as {1} ...'.format(fname, clean_fname))
        for i in range(1, 4):
            print('    Attempt number ' + str(i))
            with pysftp.Connection(self.HOST, username=self.USER, password=self.PASSWORD, cnopts=self.cnopts) as sftp:
                sftp.get(remotepath, localpath)
            try:
                Auxhist(localpath)
                print('... done')
                break
            except:
                os.remove(localpath)
                print('The download number {:d} did not work'.format(i))

    def get_files(self, fnames):
        for fname in fnames:
            self.get_file(fname)

    def get_missing_files(self):
        self.get_files(self.id_missing_files())
