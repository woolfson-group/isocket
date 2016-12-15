import os
from flask_testing import TestCase

from isocket.factory import create_app
from isocket.extensions import db
from isocket.populate_models import populate_cutoff, populate_atlas, remove_pdb_code
from isocket.models import CutoffDB, AtlasDB, PdbDB, PdbeDB, GraphDB
from isocket.graph_theory import AtlasHandler
from isocket.tombstone_update import CodesToAdd

os.environ['ISOCKET_CONFIG'] = 'testing'
_mode = 'testing'


class BaseTestCase(TestCase):

    def create_app(self):
        app = create_app()
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class CutoffDBTestCase(BaseTestCase):
    def test_cutoff_rows(self):
        populate_cutoff()
        cutoff_count = db.session.query(CutoffDB).count()
        self.assertEqual(cutoff_count, 28)


class AtlasDBTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.graph_list = AtlasHandler().atlas_graphs

    def test_first_element_of_graph_list(self):
        self.assertTrue(self.graph_list[0].name == 'G0')

    def test_populate_singleton(self):
        c = db.session.query(AtlasDB).filter(AtlasDB.name == 'G0').count()
        self.assertEqual(c, 0)
        g = self.graph_list[0]
        populate_atlas(graph_list=[g])
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


class CodesToAddTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        populate_cutoff()
        populate_atlas(graph_list=AtlasHandler().atlas_graphs)
        self.codes = ['2ebo', '10gs']
        self.cta = CodesToAdd(codes=self.codes, store_files=False)
        self.cta.run_update()

    def test_pdb_added(self):
        c = db.session.query(PdbDB).count()
        self.assertEqual(c, len(self.codes))

    def test_graphs_added(self):
        kg_len = len(self.cta.knob_graphs)
        c = db.session.query(GraphDB).count()
        self.assertEqual(kg_len, c)

    def test_pdbe_added(self):
        c = db.session.query(PdbeDB).count()
        self.assertEqual(c, len(self.codes))

    def test_graph_names(self):
        q = db.session.query(GraphDB, AtlasDB).join(AtlasDB)
        c = q.filter(AtlasDB.name == 'G7').count()
        self.assertEqual(c, 3)
        c = q.filter(AtlasDB.name == 'G17').count()
        self.assertEqual(c, 1)
        c = q.filter(AtlasDB.name == 'G163').count()
        self.assertEqual(c, 16)


class RemovePdbCodeTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        populate_cutoff()
        populate_atlas(graph_list=AtlasHandler().atlas_graphs)
        self.code = '2ebo'
        # add pdb code
        CodesToAdd(codes=[self.code], store_files=False).run_update()
        remove_pdb_code(code=self.code)

    def test_pdb_code_is_gone(self):
        q = db.session.query(PdbDB).filter(PdbDB.pdb == self.code)
        p = q.one_or_none()
        self.assertIsNone(p)

    def test_graphs_are_gone(self):
        c = db.session.query(GraphDB).count()
        self.assertEqual(c, 0)


