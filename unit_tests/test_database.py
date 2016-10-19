import os
from flask_testing import TestCase

from isocket_app.factory import create_app
from isocket_app.extensions import db
from isocket_app.populate_models import populate_cutoff, populate_atlas, add_to_atlas, graph_list
from isocket_app.models import CutoffDB, AtlasDB

os.environ['ISOCKET_CONFIG'] = 'testing'


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

    def test_first_element_of_graph_list(self):
        self.assertTrue(graph_list[0].name == 'G0')

    def test_add_to_atlas(self):
        c = db.session.query(AtlasDB).filter(AtlasDB.name == 'G0').count()
        self.assertEqual(c, 0)
        g = graph_list[0]
        add_to_atlas(graph=g)
        c = db.session.query(AtlasDB).filter(AtlasDB.name == 'G0').count()
        self.assertEqual(c, 1)

    def test_populate_atlas(self):
        c = db.session.query(AtlasDB).count()
        self.assertEqual(c, 0)
        populate_atlas()
        c = db.session.query(AtlasDB).count()
        self.assertEqual(c, len(graph_list))

"""
class AddPdbCodeTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.code = '2ebo'
        add_pdb_code(code=self.code)

    def test_pdb_code_exists(self):
        q = db.session.query(PdbDB).filter(PdbDB.pdb == self.code)
        p = q.one()
        self.assertEqual(p.pdb, self.code)

    def test_pdbe_exists(self):
        c = db.session.query(PdbeDB).count()
        self.assertEqual(c, 1)


class RemovePdbCodeTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.code = '2ebo'
        add_pdb_code(code=self.code)
        remove_pdb_code(code=self.code)

    def test_pdb_code_is_gone(self):
        q = db.session.query(PdbDB).filter(PdbDB.pdb == self.code)
        p = q.one_or_none()
        self.assertIsNone(p)
"""


class CutoffDBTestCase(BaseTestCase):

    def test_cutoff_rows(self):
        populate_cutoff()
        cutoff_count = db.session.query(CutoffDB).count()
        self.assertEqual(cutoff_count, 28)
