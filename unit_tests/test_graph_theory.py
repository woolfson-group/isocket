import unittest
import pickle
import networkx
import numpy
from networkx.generators import cycle_graph, complete_graph

from isocket_settings import global_settings
from isocket.graph_theory import AtlasHandler, GraphHandler, isomorphism_checker, sorted_connected_components

mode = 'testing'
unknown_graphs = global_settings["unknown_graphs"][mode]


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


class GraphHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.g1 = complete_graph(8)
        self.g2 = complete_graph(9)
        self.g1_name = 'U1'
        self.g2_name = 'jack_test_graph'

    def clear_unknown_graphs(self):
        with open(unknown_graphs, 'wb') as foo:
            pickle.dump([], foo)

    def tearDown(self):
        self.clear_unknown_graphs()

    def test_complete_graph(self):
        gh = GraphHandler(g=self.g1, mode=mode)
        self.assertIsNone(gh.name)
        gh2 = GraphHandler(g=self.g2, mode=mode)
        self.assertIsNone(gh2.name)

    def test_graph_parameters(self):
        gh = GraphHandler(g=self.g1, mode=mode)
        self.assertEqual(gh.graph_parameters()['nodes'], 8)
        self.assertEqual(gh.graph_parameters()['edges'], 28)

    def test_isomorphism_checker_with_atlas_handler(self):
        self.clear_unknown_graphs()
        g1 = self.g1.copy()
        g1.name = self.g1_name
        g2 = self.g2.copy()
        g2.name = self.g2_name
        graph_list = [g1, g2]
        self.assertEqual(isomorphism_checker(self.g1, graph_list=graph_list), self.g1_name)
        self.assertEqual(isomorphism_checker(self.g2, graph_list=graph_list), self.g2_name)


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


class SortedConnectedComponentsTestCase(unittest.TestCase):
    """Tests for isambard.tools.graph_theory.sorted_connected_components. """

    def test_number_of_disjoint_cycles(self):
        """Graph of k disjoint cycles should have k connected components."""
        n = numpy.random.randint(4, 100)
        cycles = [networkx.cycle_graph(x) for x in range(3, n)]
        g = networkx.disjoint_union_all(cycles)
        self.assertEqual(len(sorted_connected_components(g)), len(cycles))

    def test_number_of_trivial_nodes(self):
        """Graph with no edges should have 0 connected components."""
        n = numpy.random.randint(1, 100)
        g = networkx.Graph()
        g.add_nodes_from(list(range(n)))
        self.assertEqual(len(sorted_connected_components(g, include_trivials=False)), 0)
        self.assertEqual(len(sorted_connected_components(g, include_trivials=True)), n)

    def test_cc_cyclic(self):
        """Largest connected component of a cyclic graph should be itself."""
        n = numpy.random.randint(3, 101)
        cycle = cycle_graph(n)
        cc0 = sorted_connected_components(cycle)[0]
        aet = networkx.is_isomorphic(cycle, cc0)
        self.assertTrue(aet)

    def test_cc_two_cycles(self):
        g = networkx.disjoint_union(cycle_graph(4), cycle_graph(3))
        components = sorted_connected_components(g)
        cc_nodes = [x.number_of_nodes() for x in components]
        self.assertTrue(numpy.allclose(cc_nodes, [4, 3]))

    def test_non_trivial(self):
        """Add trivial nodes: these should be removed by call to get_connected_component."""
        g = networkx.cycle_graph(5)
        g.add_nodes_from([5, 6, 7, 8])
        components = sorted_connected_components(g, include_trivials=False)
        self.assertEqual(components[0].nodes(), list(range(5)))

__author__ = 'Jack W. Heal'
