import sqlalchemy
import itertools
from contextlib import contextmanager
import pickle

from isocket_settings import global_settings
from isocket_app.graph_theory import GraphHandler, isomorphism_checker
from isocket_app.models import db, GraphDB, PdbDB, PdbeDB, CutoffDB, AtlasDB
from isocket_app.structure_handler import StructureHandler


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
    scuts = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
    kcuts = list(range(4))
    with session_scope() as session:
        for kcut, scut in itertools.product(kcuts, scuts):
            PopulateModel(CutoffDB, kcut=kcut, scut=scut).go(session)


def add_pdb_code(code, mmol=None, mode='production'):
    # If pdb is already in database, exit before doing anything.
    with session_scope() as session:
        pdb = session.query(PdbDB).filter(PdbDB.pdb == code).one_or_none()
        if pdb is not None:
            return
    structure = StructureHandler.from_code(code=code, mmol=mmol)
    atlas_graphs = structure.get_atlas_graphs(mode=mode)
    for ag in atlas_graphs:
        if ag.name is None:
            # add to holding list
            add_g_to_holding_pickle(g=ag, mode=mode)
        else:
            add_graph_to_db(**ag.graph)
    return


def add_g_to_holding_pickle(g, mode='production'):
    holding_pickle = global_settings["holding_unknowns"][mode]
    with open(holding_pickle, 'rb') as foo:
        try:
            hp = pickle.load(foo)
        except EOFError:
            hp = []
    hp.append(g)
    with open(holding_pickle, 'wb') as foo:
        pickle.dump(hp, foo)
    return


def process_holding_pickle(mode='production'):
    holding_pickle = global_settings["holding_unknowns"][mode]
    unknown_pickle = global_settings["unknown_graphs"][mode]
    with open(unknown_pickle, 'rb') as foo:
        try:
            unknown_pickle_list = pickle.load(foo)
        except EOFError:
            unknown_pickle_list = []
    with open(holding_pickle, 'rb') as foo:
        try:
            holding_pickle_list = pickle.load(foo)
        except EOFError:
            holding_pickle_list = []
    if len(unknown_pickle_list) > 0:
        next_number_to_add = max([int(x.name[1:]) for x in unknown_pickle_list]) + 1
    else:
        next_number_to_add = 0
    to_add_to_atlas = []
    for i, g in enumerate(holding_pickle_list):
        n = isomorphism_checker(g, graph_list=holding_pickle_list[:i])
        if n is None:
            g.name = 'U{}'.format(next_number_to_add)
            to_add_to_atlas.append(g)
            next_number_to_add += 1
        else:
            g.name = n
    unknown_pickle_list += to_add_to_atlas
    with open(unknown_pickle, 'wb') as foo:
        pickle.dump(unknown_pickle_list, foo)
    populate_atlas(graph_list=to_add_to_atlas)
    for g in holding_pickle_list:
        add_graph_to_db(**g.graph)
    # clear holding list
    with open(holding_pickle, 'wb') as foo:
        pickle.dump([], foo)
    return


def add_graph_to_db(code, mmol, preferred, cc_num, name, kcut, scut, nodes, edges):
    with session_scope() as session:
        pdb = PopulateModel(model=PdbDB, pdb=code).go(session=session)
        pdbe = PopulateModel(model=PdbeDB, pdb_id=pdb.id, preferred=preferred, mmol=mmol).go(
            session=session)
        cutoff = session.query(CutoffDB).filter(CutoffDB.scut == scut,
                                                CutoffDB.kcut == kcut).one()
        atlas = PopulateModel(AtlasDB, name=name, nodes=nodes, edges=edges).go(session)
        PopulateModel(GraphDB, pdbe=pdbe, atlas=atlas, cutoff=cutoff, connected_component=cc_num).go(
            session=session)
    return


def remove_pdb_code(code):
    with session_scope() as session:
        q = session.query(PdbDB).filter(PdbDB.pdb == code)
        p = q.one_or_none()
        if p is not None:
            session.delete(p)
    return


def datasets_are_valid(mode='production'):
    valid = False
    with session_scope() as session:
        adbs = set([x[0] for x in session.query(AtlasDB.name).filter(AtlasDB.name.startswith('U')).all()])
    unknown_pickle = global_settings["unknown_graphs"][mode]
    unks = {x.name for x in pickle.load(open(unknown_pickle, 'rb'))}
    if len(adbs - unks) == 0:
        valid = True
    # run checks and return True if they pass.
    # Checks: is db consistent with shelf? Check graph properties and names.
    return valid


def get_or_create(model, session, **kwargs):
    """Uses kwargs to get instance of model. If can't get that instance from session, add it to session.

    Notes
    -----
    This is an analogue to the Django function get_or_create, written for sqlalchemy.
    Implements sqlalchemy query function one_or_none(). See:
        http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.one_or_none
    Code adapted from a response to a question on Stack Overflow:
        http://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
    Posted by stackoverflow.com user Wolph:
        http://stackoverflow.com/users/54017/wolph

    Parameters
    ----------
    session : session
        An sqlalchemy session.
    model : Base
        An sqlalchemy table.
    kwargs : dict or specified keyword=value pairs
        key/value pairs used to instantiate the model.

    Returns
    -------
    2-tuple:
        First element of tuple is instance of model instantiated by **kwargs
        Second element of tuple is bool:
            True if instance has been added to session.
            False is instance was already present.

    Raises
    ------
    sqlalchemy.orm.exc.MultipleResultsFound
        If query selects multiple objects.
    """
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, sqlalchemy.sql.expression.ClauseElement))
        instance = model(**params)
        session.add(instance)
        # Need this step to retrieve automatically populated columns, i.e., the assigned id
        instance = session.query(model).filter_by(**kwargs).one()
        return instance, True