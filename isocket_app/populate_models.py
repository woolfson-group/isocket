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
        item = get_or_create(model=self.model, session=session, **self.parameters)
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
        PopulateModel(AtlasDB, **ah.graph_parameters()).go(session)


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
    scuts = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
    kcuts = list(range(4))
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


def add_pdb_code(code, **kwargs):
    structure = get_structure_data(code=code, **kwargs)
    with session_scope() as session:
        PopulateModel(model=PdbDB, pdb=structure.code).go(session=session)
        pdb = session.query(PdbDB).filter(PdbDB.pdb == structure.code)
        




def add_pdb_code_old(code, session=db.session):
    pdb_db, created = get_or_create(session=session, model=PdbDB, pdb=code)
    if not created:
        return
    cutoff_dbs = session.query(CutoffDB).all()
    if len(cutoff_dbs) == 0:
        populate_cutoff(session=session)
    fs = FileSystem(code)
    pdbe_db = get_or_create(session=session, model=PdbeDB, pdb=pdb_db,
                            mmol=fs.preferred_mmol, preferred=True)[0]
    cif = fs.cifs[fs.preferred_mmol]
    a = convert_cif_to_ampal(cif, assembly_id=fs.code)
    session.commit()
    kg = KnobGroup.from_helices(a, cutoff=10.0)
    if kg is not None:
        g = kg.graph
        for cutoff_db in cutoff_dbs:
            session.rollback()
            h = kg.filter_graph(g=g, cutoff=cutoff_db.scut, min_kihs=cutoff_db.kcut)
            h = graph_to_plain_graph(g=h)
            ccs = sorted_connected_components(h)
            for cc_num, cc in enumerate(ccs):
                storage_changed = store_graph(cc)
                cc_name = get_graph_name(cc, graph_list=graph_list)
                atlas_db = None
                if not storage_changed:
                    atlas_db = session.query(AtlasDB).filter_by(name=cc_name).one_or_none()
                    # atlas_db = next(filter(lambda x: x.name == cc_name, atlas_dbs), None)
                if atlas_db is None:
                    populate_atlas()
                    atlas_db = session.query(AtlasDB).filter_by(name=cc_name).one()
                get_or_create(session=session, model=GraphDB, connected_component=cc_num, cutoff=cutoff_db,
                              atlas=atlas_db, pdbe=pdbe_db)
                session.commit()
    return


def remove_pdb_code(code, session=db.session):
    session.rollback()
    q = session.query(PdbDB).filter(PdbDB.pdb == code)
    p = q.one_or_none()
    if p is not None:
        session.delete(p)
        session.commit()
    session.rollback()
    return
