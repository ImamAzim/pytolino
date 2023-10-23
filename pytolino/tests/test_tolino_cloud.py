#!/usr/bin/env python


"""
test all the tools in tolino cloud
"""


import unittest


from pytolino.tolino_cloud import Client, PytolinoException


class TestClient(unittest.TestCase):

    """all test concerning the Client class. """

    def test_init_nopartner(self):

        with self.assertRaises(PytolinoException):
            client = Client(server_name='this tolino partner does not exists')

    def test_init_partner_config(self):
        client = Client()
        self.assertIn('server_settings', dir(client))
        n_settings = len(client.server_settings)
        self.assertGreater(n_settings, 0) 


def run_login():
    client = Client()


if __name__ == '__main__':
    run_login()

