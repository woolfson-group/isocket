import os
from flask_testing import TestCase

from isocket_app.factory import create_app
from isocket_app.extensions import db
from isocket_app.populate_models import add_pdb_code, remove_pdb_code, populate_cutoff
from isocket_app.models import PdbDB, PdbeDB, CutoffDB

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


class AddPdbCodeTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.code = '2ebo'
        add_pdb_code(code=self.code)

    def test_pdb_code_exists(self):
        q = db.session.query(PdbDB).filter(PdbDB.pdb == self.code)
        p = q.one()
        self.assertEqual(p.pdb, self.code)


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


class FixedTablesTestCase(BaseTestCase):

    def test_cutoff_rows(self):
        populate_cutoff()
        cutoff_count = db.session.query(CutoffDB).count()
        self.assertEqual(cutoff_count, 28)
