#!/usr/bin/env python


"""
test all the tools in tolino cloud
"""

import os
import unittest
import configparser


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
    CREDENTIAL_FILEPATH = os.path.join(os.path.expanduser('~'), 'credentials.ini')
    credentials = configparser.ConfigParser()
    credentials.read(CREDENTIAL_FILEPATH)
    username = credentials['DEFAULT']['username']
    password = credentials['DEFAULT']['password']

    client = Client()


if __name__ == '__main__':
    run_login()

