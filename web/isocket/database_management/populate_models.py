import itertools
from contextlib import contextmanager

import sqlalchemy

from isocket.database_management.models import db, GraphDB, PdbDB, PdbeDB, CutoffDB, AtlasDB


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


def populate_atlas(graph_list):
    """ Add all graphs not yet in AtlasDB to AtlasDB

    Parameters
    ----------
    graph_list: list(networkx.Graph)
        Each graph must have a g.name attribute.

    Returns
    -------
    None
    """
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
    scuts = [7.0, 7.5, 8.0, 8.5, 9.0]
    kcuts = list(range(4))
    with session_scope() as session:
        for kcut, scut in itertools.product(kcuts, scuts):
            PopulateModel(CutoffDB, kcut=kcut, scut=scut).go(session)
    return


def add_graph_to_db(code, mmol, preferred, cc_num, name, kcut, scut, nodes, edges):
    """ Populates PdbDB, PdbeDB, AtlasDB (if necessary) and GraphDB with input data

    Parameters
    ----------
    code: str
        4-letter PDB accession code
    mmol: int
        Number of the biological unit
    preferred: bool
        True if the number of the preferred biological unit == mmol
    cc_num: int
        Connected component number
    name: str
        Name of the graph in the Atlas
    kcut: int
        Knob cutoff
    scut: float
        iSocket cutoff
    nodes: int
        Number of nodes in the graph
    edges: int
        Number of edges in the graph

    Returns
    -------
    None
    """
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
    """ Remove all data associated with the given PDB accession code.

    Parameters
    ----------
    code: str
        4-letter PDB accession code

    Returns
    -------
    None

    """
    with session_scope() as session:
        q = session.query(PdbDB).filter(PdbDB.pdb == code)
        p = q.one_or_none()
        if p is not None:
            session.delete(p)
    return


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
