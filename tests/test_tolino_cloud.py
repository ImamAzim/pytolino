#!/usr/bin/env python


"""
test all the tools in tolino cloud
"""

import os
import unittest
import configparser
import logging
import time
import logging
import getpass
from pathlib import Path
import tomllib


from pytolino.tolino_cloud import Client, PytolinoException, ExpirationError


TEST_EPUB = 'basic-v3plus2.epub'


# logging.basicConfig(level=logging.INFO)


class TestClient(unittest.TestCase):

    """all test concerning the Client class. """

    @classmethod
    def setUpClass(cls):
        cls.client = Client()

    def test_store_retrieve_token_error(self):
        refresh_token = 'test_token'
        hardware_id = 'test_hw_id'
        test_account = 'test_account'
        Client.store_token(test_account, refresh_token, -1, hardware_id)
        with self.assertRaises(ExpirationError):
            Client().retrieve_token(test_account)

    def test_store_retrieve_token(self):
        refresh_token = 'test_token'
        hardware_id = 'test_hw_id'
        test_account = 'test_account'
        Client.store_token(test_account, refresh_token, 10, hardware_id)
        client = Client()
        client.retrieve_token(test_account)
        retrieved_token = client.refresh_token
        retrieved_hardware_id = client.hardware_id
        self.assertEqual(refresh_token, retrieved_token)
        self.assertEqual(hardware_id, retrieved_hardware_id)
        Client.store_token(test_account, refresh_token, -1, hardware_id)

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
        username = input('username')
        password = getpass.getpass()
    return username, password


def client_method_tests():

    client = Client('www.orellfuessli.ch')
    username, password = get_test_credentials(client.server_name)
    try:
        # reuse_access_token(client)
        fp = Path(__file__).parent / 'token.toml'
        client.login(username, password, fp=fp)
    except PytolinoException as e:
        print(e)
    else:
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


EPUB_ID_PATH = Path(__file__).parent / 'epub_id'

def reuse_access_token(client):
    fp = Path(__file__).parent / 'token.toml'
    with open(fp.as_posix(), 'rb') as f:
        data = tomllib.load(f)
    refresh_token = data['refresh_token']
    hw_id = data['hardware_id']
    client.refresh_token = refresh_token
    client.hardware_id = hw_id


def upload_test():

    epub_fp = Path(__file__).parent / TEST_EPUB

    client = Client('www.orellfuessli.ch')
    username, password = get_test_credentials(client.server_name)
    fp = Path(__file__).parent / 'token.toml'
    client.login(username, password, fp=fp)
    # client.register()
    ebook_id = client.upload(epub_fp.as_posix())
    print(ebook_id)
    with open(EPUB_ID_PATH, 'w') as myfile:
        myfile.write(ebook_id)
    # client.unregister()
    # client.logout()

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

    client = Client('www.orellfuessli.ch')
    username, password = get_test_credentials(client.server_name)
    fp = Path(__file__).parent / 'token.toml'
    client.login(username, password, fp=fp)
    # username, password = get_credentials()
    # client = Client()
    # client.login(username, password)
    client.delete_ebook(epub_id)
    # client.logout()


def inventory_test():

    username, password = get_credentials()
    client = Client()
    client.login(username, password)
    client.register()
    inventory = client.get_inventory()
    client.unregister()
    client.logout()
    print(inventory[0].keys())
    for item in inventory:
        metadata = item['epubMetaData']
        print(metadata['title'])
        # print(metadata.keys())


def metadata_test():

    metadata = dict(
            title='mytitle',
            isbn='myisbn',
            language='mylanguage',
            author='myauthor',
            publisher='mypublisher',
            issued=time.time(),
            )
    with open(EPUB_ID_PATH, 'r') as myfile:
        epub_id = myfile.read()

    username, password = get_credentials()
    client = Client()
    client.login(username, password)
    client.register()

    client.upload_metadata(epub_id, **metadata)

    inventory = client.get_inventory()
    book = [el for el in inventory if el['epubMetaData']['identifier']==epub_id][0]
    online_metadata = book['epubMetaData']
    for key in metadata:
        print(key, online_metadata[key])

    client.unregister()
    client.logout()

def add_cover_test():

    cover_path = os.path.join(
            os.path.expanduser('~'),
            'cover.jpg',
            )

    with open(EPUB_ID_PATH, 'r') as myfile:
        epub_id = myfile.read()

    username, password = get_credentials()
    client = Client()
    client.login(username, password)
    client.add_cover(epub_id, cover_path)
    client.logout()

def get_test_credentials(server_name: str):
    from varboxes import VarBox
    vb = VarBox('pytolino')
    if not hasattr(vb, 'credentials'):
        vb.credentials = dict()
    if server_name in vb.credentials:
        vb.credentials[server_name]: dict
        username = vb.credentials[server_name].get('username')
        password = vb.credentials[server_name].get('password')
    else:
        username = input('username: ')
        password = getpass.getpass()
        vb.credentials[server_name] = dict(
                username=username,
                password=password,
                )
        vb.save()
    return username, password

def del_test_credentials(server_name: str):
    from varboxes import VarBox
    vb = VarBox('pytolino')
    if hasattr(vb, 'credentials'):
        if server_name in vb.credentials:
            del vb.credentials[server_name]
            vb.save()


def refresh_token():
    account_name = 'real_test_token'
    partner = 'www.orellfuessli.ch'
    client = Client(partner)
    try:
        client.get_new_token(account_name)
    except PytolinoException:
        print(f'login on your browser at {partner} and get the token.')
        refresh_token = input('refresh token:\n')
        expires_in = input('expires_in:\n')
        hardware_id = input('hardware id:\n')
        Client.store_token(account_name, refresh_token, expires_in, hardware_id)


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    # del_test_credentials('www.buecher.de')
    # cred = get_test_credentials('www.buecher.de')
    # print(cred)
    # register_test()
    # unregister_test()
    # client_method_tests()
    # upload_test()
    # delete_test()
    # add_cover_test()
    # metadata_test()
    # inventory_test()
    refresh_token()
