import unittest

from manage_ftp import AuxSFTP


class TestFTP(unittest.TestCase):

    def test_list_files(self):
        obj = AuxSFTP()
        self.assertTrue(obj.list_sftp_files())

    def test_get_missing_files(self):
        obj = AuxSFTP()
        self.assertTrue(obj.get_missing_files())


if __name__ == '__main__':
    unittest.main()
