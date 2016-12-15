from isocket.structure_handler import StructureHandler
from isocket.graph_theory import AtlasHandler, isomorphism_checker, graph_to_plain_graph
from isocket.populate_models import populate_atlas, add_graph_to_db
from collections import Counter


class CodesToAdd:
    def __init__(self, codes=None, store_files=False):
        self.store_files = store_files
        self.codes = codes

    @property
    def structure_handlers(self):
        return [StructureHandler.from_code(code=code, store_files=self.store_files) for code in self.codes]

    @property
    def knob_graphs(self):
        kgs = []
        for sh in self.structure_handlers:
            try:
                kgs.append(sh.get_knob_graphs(min_scut=7.0, max_scut=9.0, scut_increment=0.5))
            except:
                continue
        return kgs


def all_graphs_named(knob_graphs):
    return all([x.name is not None for x in knob_graphs])


def all_graph_dicts_valid(knob_graphs):
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
    a = all([compare(x.graph.keys(), key_names) for x in knob_graphs])
    b = all_graphs_named(knob_graphs=knob_graphs)
    return a and b


def name_against_unkowns(knob_graphs):
    large_graph_list = AtlasHandler().get_graph_list(atlas=False, cyclics=False, paths=False, unknowns=True)
    for g in knob_graphs:
        if g.graph['name'] is None:
            name = isomorphism_checker(g, graph_list=large_graph_list)
            if name is not None:
                g.graph['name'] = name
    return


def add_unknowns(knob_graphs):
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
    populate_atlas(graph_list=to_add_to_atlas)
    return


def add_knob_graphs_to_db(knob_graphs):
    assert all_graph_dicts_valid(knob_graphs=knob_graphs)
    for g in knob_graphs:
        add_graph_to_db(**g.graph)
    return
