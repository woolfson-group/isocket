import pickle
import unittest
import os

from networkx.generators import cycle_graph, complete_graph

from web.isocket.graph_theory import AtlasHandler, isomorphism_checker
from web.isocket_settings import global_settings

mode = 'testing'
unknown_graphs = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unknown_graphs_tests.p')
#unknown_graphs = global_settings["unknown_graphs"][mode]


class AtlasHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.atlas_handler = AtlasHandler(mode=mode)
        self.g1 = complete_graph(8)
        self.g2 = complete_graph(9)
        self.g1_name = 'U1'
        self.g2_name = 'jack_test_graph'

    def clear_unknown_graphs(self):
        with open(unknown_graphs, 'wb') as foo:
            pickle.dump([], foo)

    def tearDown(self):
        self.clear_unknown_graphs()

    def test_atlas_graphs(self):
        self.assertEqual(len(self.atlas_handler.atlas_graphs), 1253)

    def test_cyclic_graphs(self):
        self.assertEqual(len(self.atlas_handler.cyclic_graphs(max_nodes=88)), 81)

    def test_path_graphs(self):
        self.assertEqual(len(self.atlas_handler.path_graphs(max_nodes=88)), 81)


class IsomorphismCheckerTestCase(unittest.TestCase):
    """Tests for graph_theory.isomorphism_checker"""
    def setUp(self):
        self.graph_list = AtlasHandler(mode=mode).get_graph_list()

    def test_octomer(self):
        octamer = cycle_graph(8)
        self.assertEqual(isomorphism_checker(octamer, graph_list=self.graph_list), "C8")

    def test_pentamer(self):
        pent = cycle_graph(5)
        self.assertEqual(isomorphism_checker(pent), "G38")

    def test_complete_graph(self):
        g = complete_graph(8)
        self.assertIsNone(isomorphism_checker(g))

__author__ = 'Jack W. Heal'
