import networkx
from networkx.generators.atlas import graph_atlas_g
from networkx.generators import cycle_graph, path_graph
import shelve


from isocket_settings import global_settings


class AtlasHandler:
    def __init__(self, shelf_mode='production'):
        self.shelf_mode = shelf_mode

    @property
    def atlas_graphs(self):
        graph_list = graph_atlas_g()
        return graph_list

    @property
    def unknown_graphs(self):
        shelf_name = global_settings['unknown_graphs'][self.shelf_mode]
        with shelve.open(shelf_name) as shelf:
            graph_list = list(shelf.values())
        return graph_list

    def cyclic_graphs(self, max_nodes):
        graph_list = []
        for n in range(8, max_nodes + 1):
            g = cycle_graph(n)
            g.name = 'C{}'.format(n)
            graph_list.append(g)
        return graph_list

    def path_graphs(self, max_nodes):
        graph_list = []
        for n in range(8, max_nodes + 1):
            g = path_graph(n)
            g.name = 'P{}'.format(n)
            graph_list.append(g)
        return graph_list

    def get_graph_list(self, atlas=True, cyclics=True, paths=False, unknowns=False, max_cyclics=100, max_paths=100):
        graph_list = []
        if atlas:
            graph_list = self.atlas_graphs
        if cyclics:
            graph_list += self.cyclic_graphs(max_nodes=max_cyclics)
        if paths:
            graph_list += self.path_graphs(max_nodes=max_paths)
        if unknowns:
            graph_list += self.unknown_graphs
        return graph_list


class GraphHandler(AtlasHandler):
    def __init__(self, g, shelf_mode='production'):
        super().__init__(shelf_mode=shelf_mode)
        self.g = graph_to_plain_graph(g)
        self.name = self.get_graph_name()

    def get_graph_name(self):
        if self.g.graph['name'] == 'unnamed':
            name = isomorphism_checker(self.g, graph_list=self.get_graph_list(atlas=True, cyclics=True,
                                                                          paths=True, unknowns=False))

            if name is None:
                name = isomorphism_checker(self.g, graph_list=self.unknown_graphs)
                if name is None:
                    shelf_name = global_settings['unknown_graphs'][self.shelf_mode]
                    with shelve.open(shelf_name, writeback=True) as shelf:
                        name = 'U{}'.format(len(shelf) + 1)
                        assert name not in shelf
                        self.g.graph['name'] = name
                        shelf[name] = self.g.copy()
                        shelf.sync()
            self.g.graph['name'] = name
        else:
            name = self.g.graph['name']
        return name

    def graph_parameters(self):
        return dict(name=self.name, nodes=self.g.number_of_nodes(), edges=self.g.number_of_edges())


def graph_to_plain_graph(g):
    # construct h fully in case of unorderable/unsortable edges.
    h = networkx.Graph()
    h.add_nodes_from(range(len(g.nodes())))
    edges = [(g.nodes().index(e1), g.nodes().index(e2)) for e1, e2 in g.edges()]
    h.add_edges_from(edges)
    h.graph['name'] = 'unnamed'
    return h


def isomorphism_checker(g, graph_list=None):
    """ Finds the name of the graph by checking for isomorphism with the graphs in the graph_list.

    Notes
    -----
    If g is a MultiGraph, a DiGraph or a MultiDiGraph, the isomorphism is run against the underlying Graph.
    In other words, all the edge annotations (including directions) are ignored.

    Parameters
    ----------
    g : A networkx Graph.
    graph_list :
        A list of networkx.Graph objects against which to check for isomorphism.
        If the graphs in the list do not have names, then their index will be returned as a string

    Returns
    -------
    iso_name : str, or None
        The name of the graph from the graph_list that is isomorphic to g.
        If the graph does not have a 'name' attribute, its index in the list will be returned as a string.
        None if no such isomorph is found in the list_of_graphs.

    """
    if graph_list is None:
        graph_list = graph_atlas_g()
    # run isomorphism check on the Graph of g (i.e. not the DiGraph or MultiGraph).
    h = graph_to_plain_graph(g)
    isomorph = next(filter(lambda x: networkx.is_isomorphic(h, x), graph_list), None)
    if isomorph is None:
        return
    else:
        iso_name = isomorph.name
        if iso_name is None:
            iso_name = str(graph_list.index(isomorph))
    return iso_name


def sorted_connected_components(g, include_trivials=False):
    """ List of connected component subgraphs of graph g, ordered in decreasing number of nodes.

    Parameters
    ----------
    g : networkx.Graph
    include_trivials : bool
        If True, trivial connected components (i.e. singular nodes) will be included.

    Returns
    -------
    [networkx.Graph]
        List of connected component subgraphs.
    """
    h = graph_to_plain_graph(g)
    components = sorted(networkx.connected_component_subgraphs(h, copy=False),
                        key=lambda x: len(x.nodes()), reverse=True)
    if not include_trivials:
        components = [x for x in components if len(x.nodes()) > 1]
    return components


__author__ = 'Jack W. Heal'

