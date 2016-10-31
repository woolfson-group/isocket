import os
from flask_testing import TestCase

from isocket_settings import global_settings
from isocket_app.factory import create_app
from isocket_app.extensions import db
from isocket_app.populate_models import populate_cutoff, populate_atlas, add_to_atlas, add_pdb_code_2, \
    remove_pdb_code
from isocket_app.models import CutoffDB, AtlasDB, PdbDB, PdbeDB, GraphDB
from isocket_app.graph_theory import AtlasHandler

os.environ['ISOCKET_CONFIG'] = 'testing'
holding_unknowns = global_settings["holding_unknowns"]["testing"]
unknown_graphs = global_settings["unknown_graphs"]["testing"]


class BaseTestCase(TestCase):

    def create_app(self):
        app = create_app()
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class AtlasDBTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.graph_list = AtlasHandler().atlas_graphs

    def test_first_element_of_graph_list(self):
        self.assertTrue(self.graph_list[0].name == 'G0')

    def test_add_to_atlas(self):
        c = db.session.query(AtlasDB).filter(AtlasDB.name == 'G0').count()
        self.assertEqual(c, 0)
        g = self.graph_list[0]
        add_to_atlas(graph=g)
        c = db.session.query(AtlasDB).filter(AtlasDB.name == 'G0').count()
        self.assertEqual(c, 1)

    def test_populate_atlas(self):
        c = db.session.query(AtlasDB).count()
        self.assertEqual(c, 0)
        populate_atlas(graph_list=self.graph_list)
        c = db.session.query(AtlasDB).count()
        self.assertEqual(c, len(self.graph_list))

    def test_populate_atlas_run_multiple_times(self):
        populate_atlas(graph_list=self.graph_list)
        c = db.session.query(AtlasDB).count()
        self.assertEqual(c, len(self.graph_list))
        populate_atlas(graph_list=self.graph_list)
        c = db.session.query(AtlasDB).count()
        self.assertEqual(c, len(self.graph_list))


class AddPdbCodeTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        populate_cutoff()
        populate_atlas(graph_list=AtlasHandler().atlas_graphs)
        self.code = '2ebo'
        add_pdb_code_2(code=self.code, holding_pickle=holding_unknowns)

    def test_pdb_code_exists(self):
        q = db.session.query(PdbDB).filter(PdbDB.pdb == self.code)
        p = q.one()
        self.assertEqual(p.pdb, self.code)

    def test_pdbe_exists(self):
        c = db.session.query(PdbeDB).count()
        self.assertEqual(c, 1)

    def test_graph_db(self):
        q = db.session.query(GraphDB, AtlasDB).join(AtlasDB)
        c = q.filter(AtlasDB.name == 'G7').count()
        self.assertEqual(c, 3)
        c = q.filter(AtlasDB.name == 'G17').count()
        self.assertEqual(c, 1)
        c = q.filter(AtlasDB.name == 'G163').count()
        self.assertEqual(c, 24)

    def test_10gs(self):
        code = '10gs'
        add_pdb_code_2(code=code, holding_pickle=holding_unknowns)
        q = db.session.query(PdbDB).filter(PdbDB.pdb == code).one()
        self.assertEqual(q.pdb, code)


class RemovePdbCodeTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        populate_cutoff()
        populate_atlas(graph_list=AtlasHandler().atlas_graphs)
        self.code = '2ebo'
        add_pdb_code_2(code=self.code, holding_pickle=holding_unknowns)
        remove_pdb_code(code=self.code)

    def test_pdb_code_is_gone(self):
        q = db.session.query(PdbDB).filter(PdbDB.pdb == self.code)
        p = q.one_or_none()
        self.assertIsNone(p)

    def test_graphs_are_gone(self):
        c = db.session.query(GraphDB).count()
        self.assertEqual(c, 0)


class CutoffDBTestCase(BaseTestCase):

    def test_cutoff_rows(self):
        populate_cutoff()
        cutoff_count = db.session.query(CutoffDB).count()
        self.assertEqual(cutoff_count, 28)
