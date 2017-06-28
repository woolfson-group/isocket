import pickle
from collections import Counter

from isocket_settings import global_settings
from isocket.structure_handler import StructureHandler
from isocket.graph_theory import AtlasHandler, isomorphism_checker, graph_to_plain_graph
from isocket.database_management.populate_models import populate_atlas, add_graph_to_db


class UpdateCodes:
    """ Class for updating database with data associated with list of PDB accession codes """
    def __init__(self, codes=None, store_files=False):
        self.store_files = store_files
        self.codes = codes

    def __repr__(self):
        if len(self.codes) <= 3:
            codes_repr = '{}'.format(self.codes)
        else:
            codes_repr = '{}...'.format(self.codes[:3])
        return '<UpdateCodes({})>'.format(codes_repr)


    @property
    def structure_handlers(self):
        """ StructureHandler instances for preferred biological unit (mmol) for each code """
        return [StructureHandler.from_code(code=code, store_files=self.store_files) for code in self.codes]

    @property
    def knob_graphs(self):
        """ Concatenates all knob_graphs associates with each code into one list """
        all_kgs = []
        for sh in self.structure_handlers:
            try:
                kgs = sh.get_knob_graphs(min_scut=7.0, max_scut=9.0, scut_increment=0.5)
                for x in kgs:
                    all_kgs.append(x)
            except:
                continue
        return all_kgs

    def run_update(self, mode=None):
        """ Gets name for each knob graph and then adds them all to the database """
        kgs = self.knob_graphs
        # is not all named, then need to turn to list of larger graphs.
        if not all_graphs_named(knob_graphs=kgs):
            # Get names from list of larger graphs
            name_against_unknowns(knob_graphs=kgs)
            # If still not named, add graphs to list of larger graphs, and write to the file.
            if not all_graphs_named(knob_graphs=kgs):
                if mode is None:
                    allowed_modes = ['production', 'testing']
                    raise ValueError('Please provide running mode for adding new unknown_graphs.'
                                     ' Currently allowed values are {}'.format(allowed_modes))
                add_unknowns(knob_graphs=kgs, mode=mode)
        add_knob_graphs_to_db(knob_graphs=kgs)
        return


def all_graphs_named(knob_graphs):
    """

    Parameters
    ----------
    knob_graphs: list(networkx.Graph)

    Returns
    -------
    True if all graphs have the .name attribute
    """
    return all([x.name is not None for x in knob_graphs])


def all_graph_dicts_valid(knob_graphs):
    """

    Parameters
    ----------
    knob_graphs: list(networkx.Graph)

    Returns
    -------
    bool:
        True if all data is ready for adding graphs to the database.
    """
    key_names = ['cc_num',
                 'code',
                 'edges',
                 'nodes',
                 'mmol',
                 'kcut',
                 'scut',
                 'name',
                 'preferred']
    a = all([Counter(x.graph.keys()) == Counter(key_names) for x in knob_graphs])
    b = all_graphs_named(knob_graphs=knob_graphs)
    return a and b


def name_against_unknowns(knob_graphs):
    """ Checks each unnamed graph for isomorphism against list of 'unknown' (large) graphs.

    Parameters
    ----------
    knob_graphs: list(networkx.Graph)

    Returns
    -------
    None
    """
    large_graph_list = AtlasHandler().get_graph_list(atlas=False, cyclics=False, paths=False, unknowns=True)
    for g in knob_graphs:
        if g.graph['name'] is None:
            name = isomorphism_checker(g, graph_list=large_graph_list)
            if name is not None:
                g.graph['name'] = name
    return


def add_unknowns(knob_graphs, mode):
    """ Name all new unknown graphs, add them to unknown_pickle and to database.

    Parameters
    ----------
    knob_graphs: list(networkx.Graph)
    mode: str
        Allowed values: 'production' or 'testing'.

    Returns
    -------
    None
    """
    large_graph_list = AtlasHandler().get_graph_list(atlas=False, cyclics=False, paths=False, unknowns=True)
    assert not all_graphs_named(knob_graphs=knob_graphs)
    assert all(isomorphism_checker(x, graph_list=large_graph_list) for x in knob_graphs)
    next_number_to_add = max([int(x.name[1:]) for x in large_graph_list]) + 1
    to_add_to_atlas = []
    for i, g in enumerate(knob_graphs):
        n = isomorphism_checker(g, graph_list=knob_graphs[:i])
        if n is None:
            h = graph_to_plain_graph(g)
            n = 'U{}'.format(next_number_to_add)
            h.name = n
            to_add_to_atlas.append(h)
            next_number_to_add += 1
        g.graph['name'] = n
    large_graph_list += to_add_to_atlas
    unknown_pickle = global_settings["unknown_graphs"][mode]
    with open(unknown_pickle, 'wb') as foo:
        pickle.dump(large_graph_list, foo)
    populate_atlas(graph_list=to_add_to_atlas)
    return


def add_knob_graphs_to_db(knob_graphs):
    """ Adds each valid knob graph g (i.e. all data in g.graph present and correct) to database

    Parameters
    ----------
    knob_graphs: list(networkx.Graph)

    Returns
    -------
    None
    """
    assert all_graph_dicts_valid(knob_graphs=knob_graphs)
    for g in knob_graphs:
        add_graph_to_db(**g.graph)
    return
