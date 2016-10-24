import itertools
from contextlib import contextmanager

from isambard_dev.databases.general_tools import get_or_create
from isocket_app.graph_theory import GraphHandler
from isocket_app.models import db, GraphDB, PdbDB, PdbeDB, CutoffDB, AtlasDB
from isocket_app.structure_handler import get_structure_data, get_graphs_from_knob_group

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


def add_to_atlas(graph):
    ah = GraphHandler(graph)
    with session_scope() as session:
        item = PopulateModel(AtlasDB, **ah.graph_parameters()).go(session)
    return item


def populate_atlas(graph_list):
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
            ah = GraphHandler(graph=g)
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
