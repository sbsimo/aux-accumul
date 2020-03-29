import unittest

from manage_ftp import MirrorSFTP


class TestMirrorSFTP(unittest.TestCase):

    def test_list_files(self):
        obj = MirrorSFTP()
        self.assertTrue(obj.list_sftp_files())

    def test_get_missing_files(self):
        obj = MirrorSFTP()
        self.assertTrue(obj.get_missing_files())


if __name__ == '__main__':
    unittest.main()
