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


from varboxes import VarBox


from pytolino.tolino_cloud import Client, PytolinoException, ExpirationError


TEST_EPUB = 'basic-v3plus2.epub'
ACCOUNT_NAME = 'real_test_token'


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

def upload_test():

    print('upload epub...')
    epub_fp = Path(__file__).parent / TEST_EPUB
    client = Client()
    client.retrieve_token(ACCOUNT_NAME)
    ebook_id = client.upload(epub_fp.as_posix())
    print(ebook_id)
    vb = VarBox('pytolino')
    vb.ebook_id = ebook_id

def collection_test():
    with open(EPUB_ID_PATH, 'r') as myfile:
        epub_id = myfile.read()

    username, password = get_credentials()
    client = Client()
    client.login(username, password)
    client.add_to_collection(epub_id, 'test_coll')
    client.logout()


def delete_test():

    print('delete last epub')
    vb = VarBox('pytolino')
    ebook_id = vb.ebook_id

    client = Client()
    client.retrieve_token(ACCOUNT_NAME)
    client.delete_ebook(ebook_id)


def inventory_test():

    print('get inventory')
    client = Client()
    client.retrieve_token(ACCOUNT_NAME)
    inventory = client.get_inventory()
    if inventory:
        print(inventory[0].keys())
        for item in inventory:
            metadata = item['epubMetaData']
            print(metadata['title'])
    else:
        print('empty')


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

    print('add cover')

    cover_path = os.path.join(
            os.path.expanduser('~'),
            'cover.jpg',
            )

    vb = VarBox('pytolino')
    ebook_id = vb.ebook_id

    client = Client()
    client.retrieve_token(ACCOUNT_NAME)
    client.add_cover(ebook_id, cover_path)

def refresh_token():
    client = Client()
    try:
        client.get_new_token(ACCOUNT_NAME)
    except PytolinoException:
        print('login on your browser and get the token.')
        refresh_token = input('refresh token:\n')
        expires_in = int(input('expires_in:\n'))
        hardware_id = input('hardware id:\n')
        Client.store_token(ACCOUNT_NAME, refresh_token, expires_in, hardware_id)
        client.get_new_token(ACCOUNT_NAME)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    refresh_token()
    upload_test()
    # add_cover_test()
    # metadata_test()
    # collection_test()
    inventory_test()
    delete_test()
    inventory_test()
