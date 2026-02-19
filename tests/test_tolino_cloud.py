#!/usr/bin/env python


"""
test all the tools in tolino cloud
"""

import unittest
import logging
import time
from pathlib import Path


from varboxes import VarBox


from pytolino.tolino_cloud import Client, PytolinoException, ExpirationError


TEST_EPUB = 'basic-v3plus2.epub'
# ACCOUNT_NAME = 'real_test_token'
ACCOUNT_NAME = 'test_token'
TEST_COVER = 'test_cover.png'


class TestClient(unittest.TestCase):

    """all test concerning the Client class. """

    @classmethod
    def setUpClass(cls):
        cls.client = Client()

    def test_store_retrieve_token_error(self):
        refresh_token = 'test_token'
        hardware_id = 'test_hw_id'
        test_account = 'test_account'
        Client.store_token(test_account, refresh_token, -1, -1, hardware_id)
        with self.assertRaises(ExpirationError):
            client = Client()
            client.retrieve_token(test_account)
            client.raise_for_access_expiration()

    def test_store_retrieve_token_error_ref(self):
        refresh_token = 'test_token'
        hardware_id = 'test_hw_id'
        test_account = 'test_account'
        Client.store_token(test_account, refresh_token, -1, -1, hardware_id)
        with self.assertRaises(ExpirationError):
            client = Client()
            client.retrieve_token(test_account)
            client.raise_for_refresh_expiration()

    def test_store_retrieve_token(self):
        refresh_token = 'test_token'
        hardware_id = 'test_hw_id'
        test_account = 'test_account'
        Client.store_token(test_account, refresh_token, 10, 10, hardware_id)
        client = Client()
        client.retrieve_token(test_account)
        retrieved_token = client.refresh_token
        retrieved_hardware_id = client.hardware_id
        self.assertEqual(refresh_token, retrieved_token)
        self.assertEqual(hardware_id, retrieved_hardware_id)
        Client.store_token(test_account, refresh_token, -1, -1, hardware_id)

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
    print('add to a collection last epub')
    vb = VarBox('pytolino')
    ebook_id = vb.ebook_id

    client = Client()
    client.retrieve_token(ACCOUNT_NAME)
    client.add_to_collection(ebook_id, 'test_coll')


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
        for item in inventory:
            metadata = item['epubMetaData']
            print(metadata['title'])
    else:
        print('empty')


def metadata_test():

    print('update metadata')
    metadata = dict(
            title='mytitle',
            isbn='myisbn',
            language='mylanguage',
            author='myauthor',
            publisher='mypublisher',
            issued=time.time(),
            )
    vb = VarBox('pytolino')
    ebook_id = vb.ebook_id

    client = Client()
    client.retrieve_token(ACCOUNT_NAME)
    client.upload_metadata(ebook_id, **metadata)

    inventory = client.get_inventory()
    book = [
            el for el in inventory if el[
                'epubMetaData']['identifier'] == ebook_id][0]
    online_metadata = book['epubMetaData']
    for key in metadata:
        print(key, online_metadata[key])


def add_cover_test():

    print('add cover')

    cover_fp = Path(__file__).parent / TEST_COVER

    vb = VarBox('pytolino')
    ebook_id = vb.ebook_id

    client = Client()
    client.retrieve_token(ACCOUNT_NAME)
    client.add_cover(ebook_id, cover_fp.as_posix())


def refresh_token(ask_new_credentials=False):
    if ask_new_credentials:
        print('login on your browser and get the token.')
        refresh_token = input('refresh token:\n')
        expires_in = int(input('expires_in:\n'))
        refresh_expires_in = int(input('refresh_expires_in:\n'))
        hardware_id = input('hardware id:\n')
        Client.store_token(
                ACCOUNT_NAME, refresh_token, expires_in, refresh_expires_in, hardware_id)
    client = Client()
    client.get_new_token(ACCOUNT_NAME)


def get_test_credentials():
    vb = VarBox('pytolino', 'test_credentials')
    if not hasattr(vb, 'username'):
        username = input('username:\n')
        password = input('password:\n')
        vb.username = username
        vb.password = password
    return vb.username, vb.password


def login_test():
    username, password = get_test_credentials()
    client = Client()
    client.login(username, password)
    # print(client.refresh_token, client.hardware_id)
    client.store_current_token('token_test')
    client.get_new_token('token_test')


if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    # refresh_token(ask_new_credentials=False)
    # upload_test()
    # add_cover_test()
    # metadata_test()
    # collection_test()
    # inventory_test()
    # delete_test()
    # inventory_test()
    login_test()
