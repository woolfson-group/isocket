import unittest
import os

from isocket_settings import global_settings
from isocket.structure_handler import StructureHandler

install_folder = global_settings['package_path']


class StructureHandlerTestCase(unittest.TestCase):
    """ Tests for the valid_backbone_distance method of Polypeptide class. """
    def setUp(self):
        self.test_codes = ['1ek9', '2ht0', '3qy1']
        self.test_files = [os.path.join(install_folder, 'unit_tests', 'testing_files', '{}.pdb'.format(x))
                           for x in self.test_codes]

    def test_from_file_classmethod(self):
        for file in self.test_files:
            sh = StructureHandler.from_file(filename=file, path=True)
            self.assertFalse(sh.is_preferred)
