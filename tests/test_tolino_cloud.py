#!/usr/bin/env python


"""
test all the tools in tolino cloud
"""

import os
import unittest
import configparser
import logging


from pytolino.tolino_cloud import Client, PytolinoException


logging.basicConfig(level=logging.INFO)


class TestClient(unittest.TestCase):

    """all test concerning the Client class. """

    @classmethod
    def setUpClass(cls):
        cls.client = Client()

    def test_init_nopartner(self):

        with self.assertRaises(PytolinoException):
            Client(server_name='this tolino partner does not exists')

    def test_init_partner_config(self):
        self.assertTrue(hasattr(self.client, 'server_settings'))
        n_settings = len(self.client.server_settings)
        self.assertGreater(n_settings, 0)

    def test_hardware_id(self):
        self.assertTrue(hasattr(self.client, 'hardware_id'))
        self.assertIsInstance(self.client.hardware_id, str)

    def test_token_vars(self):
        self.assertTrue(hasattr(self.client, 'access_token'))
        self.assertTrue(hasattr(self.client, 'refresh_token'))
        self.assertTrue(hasattr(self.client, 'token_expires'))


def get_credentials():
    CREDENTIAL_FILEPATH = os.path.join(
            os.path.expanduser('~'),
            'credentials.ini',
            )
    if os.path.exists(CREDENTIAL_FILEPATH):
        credentials = configparser.ConfigParser()
        credentials.read(CREDENTIAL_FILEPATH)
        username = credentials['DEFAULT']['username']
        password = credentials['DEFAULT']['password']
    else:
        import getpass
        username = input('username')
        password = getpass.getpass()
    return username, password


def client_method_tests():

    username, password = get_credentials()
    client = Client()
    client.login(username, password)

    print(client.access_token)
    print(client.refresh_token)
    print(client.token_expires)

    client.logout()


def register_test():

    REGISTER_CHECK_PATH = os.path.join(
            os.path.expanduser('~'),
            'device_is_registered',
            )
    if not os.path.exists(REGISTER_CHECK_PATH):
        username, password = get_credentials()
        client = Client()
        client.login(username, password)
        client.register()
        client.logout()
        open(REGISTER_CHECK_PATH, 'w').close()
    else:
        print(
                'I think this device is already registered.',
                'If you want to do it again',
                f', delete the file {REGISTER_CHECK_PATH}',
                ' and re-run this function',
                )


def unregister_test():

    username, password = get_credentials()
    client = Client()
    client.login(username, password)

    client.unregister()

    REGISTER_CHECK_PATH = os.path.join(
            os.path.expanduser('~'),
            'device_is_registered',
            )
    if os.path.exists(REGISTER_CHECK_PATH):
        os.remove(REGISTER_CHECK_PATH)

    client.logout()


EPUB_ID_PATH = os.path.join(
        os.path.expanduser('~'),
        'epub_id',
        )


def upload_test():
    EPUB_PATH = os.path.join(
            os.path.expanduser('~'),
            'news.epub',
            )

    username, password = get_credentials()
    client = Client()
    client.login(username, password)
    ebook_id = client.upload(EPUB_PATH)
    print(ebook_id)
    with open(EPUB_ID_PATH, 'w') as myfile:
        myfile.write(ebook_id)

    client.logout()

def collection_test():
    with open(EPUB_ID_PATH, 'r') as myfile:
        epub_id = myfile.read()

    username, password = get_credentials()
    client = Client()
    client.login(username, password)
    client.add_to_collection(epub_id, 'test_coll')
    client.logout()


def delete_test():

    with open(EPUB_ID_PATH, 'r') as myfile:
        epub_id = myfile.read()

    username, password = get_credentials()
    client = Client()
    client.login(username, password)
    client.delete_ebook(epub_id)
    client.logout()


def inventory_test():

    username, password = get_credentials()
    client = Client()
    client.login(username, password)
    inventory = client.get_inventory()
    client.logout()
    print(inventory[0].keys())
    metadata = inventory[0]['epubMetaData']
    print(metadata.keys())

def delete_test():

    with open(EPUB_ID_PATH, 'r') as myfile:
        epub_id = myfile.read()

    username, password = get_credentials()
    client = Client()
    client.login(username, password)
    client.delete_ebook(epub_id)
    client.logout()
if __name__ == '__main__':
    inventory_test()
