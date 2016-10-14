import os
from flask_testing import TestCase

from isocket_app.factory import create_app
from isocket_app.extensions import db
from isocket_app.populate_models import add_pdb_code, populate_cutoff
from isocket_app.models import PdbDB, CutoffDB

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


class PdbDBTestCase(BaseTestCase):

    def test_add_pdb_code(self):
        code = '2ebo'
        add_pdb_code(code, session=db.session)
        q = db.session.query(PdbDB).filter(PdbDB.pdb == code)
        p = q.one()
        self.assertEqual(p.pdb, code)


class FixedTablesTestCase(BaseTestCase):

    def test_cutoff_rows(self):
        populate_cutoff()
        cutoff_count = db.session.query(CutoffDB).count()
        self.assertEqual(cutoff_count, 28)
