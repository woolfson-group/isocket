from flask import Flask
from flask_testing import TestCase
from flask_sqlalchemy import SQLAlchemy

from isocket_app.populate_models import add_pdb_code, populate_atlas, populate_cutoff
from isocket_app.models import GraphDB, PdbDB, PdbeDB, CutoffDB, AtlasDB

class DBTest(TestCase):

    def create_app(self):
        app = Flask(__name__, instance_relative_config=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/jackheal/Projects/isocket/isocket_app/unit_tests/test_atlas.db'
        app.config['TESTING'] = True
        return app

    def setUp(self):
        self.app = self.create_app()
        self.db = SQLAlchemy(app=self.app)
        self.db.create_all()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()

    def test_basic_test(self):
        print(self.db.engine)
        self.assertTrue(self.app.config['TESTING'])

    def test_add_pdb_code(self):
        populate_cutoff()
        code = '2ebo'
        add_pdb_code(code, session=self.db.session)
        q = self.db.session.query(PdbDB).filter(PdbDB.pdb == code)
        p = q.one()
        self.assertEqual(p.pdb, code)
