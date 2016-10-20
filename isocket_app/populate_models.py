import networkx
import sqlalchemy
from collections import namedtuple
import itertools
from flask_sqlalchemy import _BoundDeclarativeMeta
from contextlib import contextmanager

from isambard_dev.add_ons.filesystem import FileSystem
from isambard_dev.add_ons.parmed_to_ampal import convert_cif_to_ampal
from isambard_dev.add_ons.knobs_into_holes import KnobGroup
from isambard_dev.databases.general_tools import get_or_create
from isambard_dev.tools.graph_theory import list_of_graphs, graph_to_plain_graph, sorted_connected_components, \
    get_graph_name, store_graph, two_core_names, get_unknown_graph_list, add_two_core_name_to_json
from isocket_app.models import db, GraphDB, PdbDB, PdbeDB, CutoffDB, AtlasDB


graph_list = list_of_graphs(unknown_graphs=True)
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
    def __init__(self, graph):
        self.graph = graph_to_plain_graph(graph)
        if graph.name and graph.name[0] != 'U':
            self.name = graph.name
        else:
            self.name = get_graph_name(graph, graph_list=graph_list)

    def graph_parameters(self):
        return dict(name=self.name, nodes=self.graph.number_of_nodes(), edges=self.graph.number_of_edges())


def add_to_atlas(graph):
    ah = AtlasHandler(graph)
    with session_scope() as session:
        item = PopulateModel(AtlasDB, **ah.graph_parameters()).go(session)
    return item


def populate_atlas():
    for g in graph_list:
        add_to_atlas(g)
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
