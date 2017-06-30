import os

from flask_testing import TestCase

from web.isocket.factory import create_app

os.environ['ISOCKET_CONFIG'] = 'testing'

class ConnectionTestCase(TestCase):

    def create_app(self):
        return create_app()

    def test_about_200(self):
        response = self.client.get('/about')
        self.assert200(response)

    def test_contact_200(self):
        response = self.client.get('/contact')
        self.assert200(response)

    def test_reference_200(self):
        response = self.client.get('/reference')
        self.assert200(response)
