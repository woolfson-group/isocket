import networkx
from networkx.generators.atlas import graph_atlas_g
from networkx.generators import cycle_graph, path_graph
import shelve


_unknown_graph_shelf = '/Users/jackheal/Projects/isocket/isocket_app/unknown_graphs'


atlas_graph_list = graph_atlas_g()


def list_of_graphs(unknown_graphs=False):
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
    graph_list = atlas_graph_list
    # cycle and path graphs
    max_n = 100
    for n in range(8, max_n + 1):
        c = cycle_graph(n)
        p = path_graph(n)
        c.name = 'C{0}'.format(n)
        p.name = 'P{0}'.format(n)
        graph_list.append(c)
        graph_list.append(p)
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


def get_unknown_graph_list():
    with shelve.open(_unknown_graph_shelf) as shelf:
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
    # if no graph_list is supplied, run list_of_graphs for the Graph Atlas list.
    if graph_list is None:
        graph_list = list_of_graphs()
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
        if name is None:
            name = 'U{0}'.format(len(unknown_graph_list) + 1)
    return name


def _add_graph_to_shelf(g):
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
    name = get_graph_name(h)
    if name[0] == 'U':
        with shelve.open(_unknown_graph_shelf) as shelf:
            if name not in shelf.keys():
                h.name = name
                shelf[name] = h
                added = True
    return added


__author__ = 'Jack W. Heal'
