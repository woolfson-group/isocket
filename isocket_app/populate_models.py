import networkx
import sqlalchemy
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
        get_or_create(model=self.model, session=session, **self.parameters)


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


"""
class PopulateCutoffDB:
    @property
    def scuts(self):
        return [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]

    @property
    def kcuts(self):
        return list(range(4))

    def go(self, session):
        for kcut, scut in itertools.product(self.kcuts, self.scuts):
            get_or_create(model=CutoffDB, session=session, scut=scut, kcut=kcut)
"""


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


def populate_atlas(session=db.session):
    """ Populate AtlasDB with graphs from the extended list_of_graphs.

    Notes
    -----
    Depends on any new graphs being in the unknown_graphs shelf and in the two_core_names dictionary.
    Running isambard.tools.graph_theory.store_graph(g) for each new graph g will accomplish this.
    Runs session.commit() at the end, so any new graphs will have been added to the atlas table.
    First adds new graphs and then subsequently fills the two_core_id.
    Skips over graphs already in AtlasDB.
    Run this function after new unknown graphs are added to the unknown_graph_shelf.

    Returns
    -------
    None

    """
    # clear session before starting - good practice.
    session.rollback()
    # Full list of all graphs in Atlas and/or encountered to date.
    # Get AtlasDB instances for graphs not currently in the coeus.atlas table. Add and commit them.
    atlas_names = [x[0] for x in session.query(AtlasDB.name).all()]
    atlas_dbs = [AtlasDB(nodes=g.number_of_nodes(), name=g.name, edges=g.number_of_edges())
                 for g in graph_list if g.name not in atlas_names]
    session.add_all(atlas_dbs)
    session.commit()
    # Fill in the two_core_id column for the recently added graphs.
    for atlas_db in atlas_dbs:
        try:
            two_core_name = two_core_names[atlas_db.name]
        except KeyError:
            g = next(filter(lambda x: x.name == atlas_db.name, get_unknown_graph_list()))
            two_core_name = get_graph_name(networkx.k_core(g, 2))
            add_two_core_name_to_json(atlas_db.name, two_core_name, force_add=False)
        two_core_db = session.query(AtlasDB).filter_by(name=two_core_name).one()
        atlas_db.two_core_id = two_core_db.id
    session.add_all(atlas_dbs)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        session.rollback()
        return 0
    return 1


def add_pdb_code(code, session=db.session):
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
