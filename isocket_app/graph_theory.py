import networkx
from networkx.generators.atlas import graph_atlas_g
from networkx.generators import cycle_graph, path_graph
import shelve


_unknown_graph_shelf = '/Users/jackheal/Projects/isocket/isocket_app/unknown_graphs'


class AtlasHandler:
    def __init__(self, shelf_name=_unknown_graph_shelf):
        self.shelf_name = shelf_name

    @property
    def atlas_graphs(self):
        graph_list = graph_atlas_g()
        return graph_list

    @property
    def unknown_graphs(self):
        with shelve.open(self.shelf_name, flag='r') as shelf:
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

    def get_next_unknown_graph_name(self):
        with shelve.open(self.shelf_name, 'r') as shelf:
            number_of_graphs = len(shelf)
        name = 'U{}'.format(number_of_graphs + 1)
        return name

    def _add_graph_to_shelf(self, g, name):
        """ Runs isomorphism checker against stored dictionary of non-Atlas graphs.

        Notes
        -----
        The dictionary of non-Atlas graphs is stored as a .db (output from shelve) file.
            Keys are unknown graph names.
            Values are dictionaries storing the unknown graphs themselves as well as some basic properties of the graphs.
        If graph is not in Atlas, nor in this dictionary of non-Atlas graphs, then it is added to this dictionary.
        Unknown graphs are named 'Un', where n is the order in which they have been encountered.
        The number n does not tell you anything about the properties of the graph.

        Parameters
        ----------
        g : A networkx Graph.

        Returns
        -------
        added : bool
            True if graph was added to shelf
        """
        added = False
        h = graph_to_plain_graph(g)
        with shelve.open(self.shelf_name, flag='w') as shelf:
            if name not in shelf.keys():
                h.name = name
                shelf[name] = h
                added = True
        return added


class GraphHandler(AtlasHandler):
    def __init__(self, graph, shelf_name=_unknown_graph_shelf):
        super().__init__(shelf_name=shelf_name)
        self.graph = graph_to_plain_graph(graph)
        self.graph.name = self.name

    @property
    def name(self):
        name = self.get_graph_name()
        if name is None:
            name = self.get_unknown_graph_name()
        return name

    def get_graph_name(self):
        name = isomorphism_checker(self.graph, graph_list=self.get_graph_list(atlas=True, cyclics=True,
                                                                              paths=True, unknowns=False))
        if name is None:
            name = isomorphism_checker(self.graph, graph_list=self.unknown_graphs)
        return name

    def get_unknown_graph_name(self):
        name = self.get_graph_name()
        if name is None:
            # process new unknown graph.
            name = self.get_next_unknown_graph_name()
            # TODO namedtuple to return item, created.
            self._add_graph_to_shelf(g=self.graph, name=name)
        return name

    def graph_parameters(self):
        return dict(name=self.name, nodes=self.graph.number_of_nodes(), edges=self.graph.number_of_edges())


def list_of_graphs(unknown_graphs=False, cyclics=True, max_cyclic=100):
    """

    Parameters
    ----------
    unknown_graphs : bool
        If True, appends the graphs from the unknown_graphs.db shelf.

    Returns
    -------
    graph_list : list(networkx.Graph)
        List of graph objects with .name attributes corresponding to their names in the Atlas of Graphs.
        These names are used in the coeus database table AtlasDB.

    """
    # atlas graphs
    graph_list = graph_atlas_g()
    # cycle and path graphs
    if cyclics:
        for n in range(8, max_cyclic + 1):
            c = cycle_graph(n)
            c.name = 'C{}'.format(n)
            graph_list.append(c)
    # Add other custom graphs here.
    # If unknown_graphs, append them to the list from shelf.
    if unknown_graphs:
        graph_list += get_unknown_graph_list()
    return graph_list


def graph_to_plain_graph(g):
    # construct h fully in case of unorderable/unsortable edges.
    h = networkx.Graph()
    h.add_nodes_from(range(len(g.nodes())))
    edges = [(g.nodes().index(e1), g.nodes().index(e2)) for e1, e2 in g.edges()]
    h.add_edges_from(edges)
    return h


def get_unknown_graph_list(shelf_name=_unknown_graph_shelf):
    with shelve.open(shelf_name, flag='r') as shelf:
        unknown_graph_list = list(shelf.values())
    return unknown_graph_list


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


def get_graph_name(g, graph_list=None):
    # construct h fully in case of unorderable/unsortable edges.
    h = graph_to_plain_graph(g)
    name = isomorphism_checker(h, graph_list=graph_list)
    if name is None:
        unknown_graph_list = get_unknown_graph_list()
        name = isomorphism_checker(h, graph_list=unknown_graph_list)
    return name



__author__ = 'Jack W. Heal'

