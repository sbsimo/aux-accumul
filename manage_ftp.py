"""A module used for mirroring a SFTP file

Export the MirrorSFTP especially conceived for the scope.
"""
import os
import configparser
import datetime

import pysftp

from wrfita_aux import WrfItaAux


class MirrorSFTP:
    """A class used for mirroring the content of the SFTP file
    to a local disk.

    Attributes:
        HOST: str
            the hostname of the SFTP
        USER: str
            the username of a valid account to the SFTP
        PASSWORD: str
            the password of a valid account to the SFTP
        remote_folder: str
            the name of the remote folder to be mirrored
        DATADIR: str
            the local folder used for mirroring the SFTP files
    """
    def __init__(self):
        self.cnopts = pysftp.CnOpts()
        self.cnopts.hostkeys = None
        self.remote_folder = 'wrf'
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.HOST = config['SFTP']['HOST']
        self.USER = config['SFTP']['USER']
        self.PASSWORD = config['SFTP']['PASSWORD']
        self.DATADIR = config['STRUCTURE']['DATADIR']

    def list_today_sftp_files(self):
        """Prepare and return a list of filenames available remotely.

        Only the filenames related to the model run
        in the current day are given.

        :return: list
        """
        # TODO test this method
        sftp_files = self.list_sftp_files()
        file_prefix = datetime.date.today().strftime(WrfItaAux.FILENAME_FORMAT)[:-1]
        return [sftp_file for sftp_file in sftp_files if sftp_file.startswith(file_prefix)]

    def list_sftp_files(self):
        """Prepare and return a list of filenames available remotely

        :return: list
        """
        with pysftp.Connection(self.HOST, username=self.USER, password=self.PASSWORD, cnopts=self.cnopts) as sftp:
            filenames = sftp.listdir(self.remote_folder)
        return filenames

    def list_local_files(self):
        """Prepare and return a list of filenames available locally

        :return: list
        """
        return os.listdir(self.DATADIR)

    def id_missing_files(self):
        """Identify missing files locally

        Compare the files available remotely on the SFTP with
        the ones available locally on disk and return
        a set of locally-missing filenames.

        :return: set
            containing the missing filenames
        """
        sftp_file_names = set(self.list_today_sftp_files())
        local_file_names = set(self.list_local_files())
        return sftp_file_names - local_file_names

    def get_file(self, fname):
        """Download the given filename from the SFTP
        with a 3-attempts policy

        :param fname: str
            the name of file to be downloaded
        :return: 0
        """
        remotepath = '/'.join([self.remote_folder, fname])
        localpath = os.path.join(self.DATADIR, fname)
        print('Saving {0} ...'.format(fname))
        for i in range(1, 4):
            print('    Attempt number ' + str(i))
            with pysftp.Connection(self.HOST, username=self.USER, password=self.PASSWORD, cnopts=self.cnopts) as sftp:
                sftp.get(remotepath, localpath)
            try:
                # verify that it is a valid netCDF4 file
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
        """Download a number of files from the SFTP

        Given an iterable of filenames, download each of them
        from the SFTP

        :param fnames: iterable
        :return: 0
        """
        for fname in fnames:
            self.get_file(fname)
        return 0

    def get_missing_files(self):
        """Download a number of files from the SFTP.

        In particular the files that are missing locally on disk.

        :return: 0
        """
        self.get_files(self.id_missing_files())
        return 0

    def clean_workdir(self):
        """Clean working directory from old files.

        Delete files that are older than the current day.

        :return: None
        """
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
