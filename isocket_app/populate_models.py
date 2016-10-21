import itertools
from collections import namedtuple
from contextlib import contextmanager

from isambard_dev.add_ons.filesystem import FileSystem
from isambard_dev.add_ons.parmed_to_ampal import convert_cif_to_ampal
from isambard_dev.add_ons.knobs_into_holes import KnobGroup
from isambard_dev.databases.general_tools import get_or_create
from isocket_app.graph_theory import list_of_graphs, graph_to_plain_graph, sorted_connected_components, \
    get_graph_name, get_next_unknown_graph_name, _add_graph_to_shelf, _unknown_graph_shelf
from isocket_app.models import db, GraphDB, PdbDB, PdbeDB, CutoffDB, AtlasDB


scuts = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
kcuts = list(range(4))


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = db.session
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class PopulateModel:
    def __init__(self, model, **kwargs):
        try:
            self.model = model
            self.instance = model(**kwargs)
            self.parameters = kwargs
        except Exception as e:
            raise e

    def go(self, session):
        item, created = get_or_create(model=self.model, session=session, **self.parameters)
        return item


class AtlasHandler:
    def __init__(self, graph, shelf_name=_unknown_graph_shelf):
        self.graph = graph_to_plain_graph(graph)
        self.shelf_name = shelf_name
        self.name = self.get_unknown_graph_name()
        """
        if graph.name and graph.name[0] != 'U':
            self.name = graph.name
        else:
            self.name = self.get_unknown_graph_name()
        """

    def get_unknown_graph_name(self):
        name = get_graph_name(self.graph)
        if name is None:
            # process new unknown graph.
            name = get_next_unknown_graph_name(shelf_name=self.shelf_name)
            _add_graph_to_shelf(g=self.graph, name=name, shelf_name=self.shelf_name)
        return name

    def graph_parameters(self):
        return dict(name=self.name, nodes=self.graph.number_of_nodes(), edges=self.graph.number_of_edges())


def add_to_atlas(graph):
    ah = AtlasHandler(graph)
    with session_scope() as session:
        item = PopulateModel(AtlasDB, **ah.graph_parameters()).go(session)
    return item


def populate_atlas(graph_list=None):
    if graph_list is None:
        graph_list = list_of_graphs(unknown_graphs=True)
    with session_scope() as session:
        s1 = set([x[0] for x in session.query(AtlasDB.name).all()])  # graph names of Atlas objects already in db.
    s2 = set([x.name for x in graph_list])
    to_add = s2 - s1  # only want to add g in graph_list if not in Atlas already.
    atlas_dbs = [AtlasDB(name=g.name, nodes=g.number_of_nodes(), edges=g.number_of_edges())
                 for g in filter(lambda x: x.name in to_add, graph_list)]
    with session_scope() as session:
        session.add_all(atlas_dbs)
    return


def populate_cutoff():
    """ Populate CutoffDB using internally-defined range of kcuts and scuts.

    Returns
    -------
    True if new values added to database
    False otherwise
    """
    with session_scope() as session:
        for kcut, scut in itertools.product(kcuts, scuts):
            PopulateModel(CutoffDB, kcut=kcut, scut=scut).go(session)


def get_structure_data(code, preferred=True, mmol=1, cutoff=10.0):
    Structure = namedtuple('Structure', ['code', 'mmol', 'preferred', 'knob_group'])
    fs = FileSystem(code=code)
    if preferred:
        mmol = fs.preferred_mmol
    cif = fs.cifs[mmol]
    a = convert_cif_to_ampal(cif, assembly_id=code)
    kg = KnobGroup.from_helices(a, cutoff=cutoff)
    return Structure(code=code, mmol=mmol, preferred=preferred, knob_group=kg)


def get_graphs_from_knob_group(knob_group):
    g = knob_group.graph
    knob_graphs = []
    for scut, kcut in itertools.product(scuts[::-1], kcuts):
        h = knob_group.filter_graph(g=g, cutoff=scut, min_kihs=kcut)
        h = graph_to_plain_graph(g=h)
        ccs = sorted_connected_components(h)
        for cc_num, cc in enumerate(ccs):
            cc.graph.update(cc_num=cc_num, scut=scut, kcut=kcut)
            knob_graphs.append(cc)
    return knob_graphs


def add_pdb_code(code, **kwargs):
    structure = get_structure_data(code=code, **kwargs)
    knob_graphs = []
    if structure.knob_group is not None:
        knob_graphs = get_graphs_from_knob_group(knob_group=structure.knob_group)
    with session_scope() as session:
        pdb = PopulateModel(model=PdbDB, pdb=structure.code).go(session=session)
        pdbe = PopulateModel(model=PdbeDB, pdb=pdb, preferred=structure.preferred, mmol=structure.mmol).go(
            session=session)
        for g in knob_graphs:
            ah = AtlasHandler(graph=g)
            cutoff = session.query(CutoffDB).filter(CutoffDB.scut == g.graph['scut'],
                                                    CutoffDB.kcut == g.graph['kcut']).one()
            atlas = PopulateModel(AtlasDB, **ah.graph_parameters()).go(session)
            PopulateModel(GraphDB, pdbe=pdbe, atlas=atlas, cutoff=cutoff, connected_component=g.graph['cc_num']).go(
                session=session)
    return


def remove_pdb_code(code):
    with session_scope() as session:
        q = session.query(PdbDB).filter(PdbDB.pdb == code)
        p = q.one_or_none()
        if p is not None:
            session.delete(p)
    return
