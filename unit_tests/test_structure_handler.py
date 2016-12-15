import unittest
import os
from collections import Counter

from isocket_settings import global_settings
from isocket.structure_handler import StructureHandler

install_folder = global_settings['package_path']


class StructureHandlerTestCase(unittest.TestCase):
    """ Tests for the valid_backbone_distance method of Polypeptide class. """
    def setUp(self):
        self.test_codes = ['1ek9', '2ht0', '3qy1']
        self.test_files = [os.path.join(install_folder, 'unit_tests', 'testing_files', '{}.pdb'.format(x))
                           for x in self.test_codes]

    def test_from_code_classmethod(self):
        for code in self.test_codes:
            sh = StructureHandler.from_code(code=code, store_files=False)
            self.assertTrue(sh.is_preferred)
            self.assertEqual(code, sh.code)

    def test_from_file_classmethod(self):
        for file in self.test_files:
            sh = StructureHandler.from_file(filename=file)
            self.assertFalse(sh.is_preferred)


class StructureHandlerGetKnobGraphsTestCase(unittest.TestCase):

    def setUp(self):
        code = '2ebo'
        self.sh = StructureHandler.from_code(code=code, store_files=False)
        self.kgs = self.sh.get_knob_graphs()

    def test_number_of_knob_graphs(self):
        self.assertTrue(len(self.kgs) == 20)

    def test_knob_graph_names(self):
        kg_names_counter = Counter([x.name for x in self.kgs])
        self.assertEqual(len(kg_names_counter), 3)
        self.assertTrue(kg_names_counter['G163'], 16)
        self.assertTrue(kg_names_counter['G7'], 3)
        self.assertTrue(kg_names_counter['G17'], 1)

    def test_graph_keys(self):
        """ Tests the knob graphs have precisely the expected set of keys in their graph dict attribute. """
        compare = lambda x, y: Counter(x) == Counter(y)
        key_names = ['cc_num',
                     'code',
                     'edges',
                     'nodes',
                     'mmol',
                     'kcut',
                     'scut',
                     'name',
                     'preferred']
        a = all([compare(x.graph.keys(), key_names) for x in self.kgs])
        self.assertTrue(a)

