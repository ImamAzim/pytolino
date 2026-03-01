#!/usr/bin/env python


"""
test all the tools in tolino cloud
"""

import unittest
import logging
import time
from pathlib import Path
import datetime


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
        cls.client = Client('username')

    def test_init_nopartner(self):
        with self.assertRaises(PytolinoException):
            Client(server_name='this tolino partner does not exists',
                   username='username')


def upload_test():

    print('upload epub...')
    epub_fp = Path(__file__).parent / TEST_EPUB
    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)
    ebook_id = client.upload(epub_fp)
    print(ebook_id)
    vb = VarBox('pytolino')
    vb.ebook_id = ebook_id


def collection_test():
    print('add to a collection last epub')
    vb = VarBox('pytolino')
    ebook_id = vb.ebook_id

    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)
    client.add_to_collection(ebook_id, 'test_coll')


def delete_test():

    print('delete last epub')
    vb = VarBox('pytolino')
    ebook_id = vb.ebook_id

    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)
    client.delete_ebook(ebook_id)


def inventory_test():

    print('get inventory')
    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)
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
    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)

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

    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)
    client.add_cover(ebook_id, cover_fp)


def login_test():
    username, password = get_test_credentials()
    client = Client(username=username)
    expiration = client.access_expiration_time
    print('access token expiration time:')
    print(datetime.datetime.fromtimestamp(expiration))
    print('login...')
    client.login(password)
    client = Client(username=username)
    expiration = client.access_expiration_time
    print('access token new expiration time:')
    print(datetime.datetime.fromtimestamp(expiration))


def get_test_credentials():
    vb = VarBox('pytolino', 'test_credentials')
    if not hasattr(vb, 'username'):
        username = input('username:\n')
        password = input('password:\n')
        vb.username = username
        vb.password = password
    return vb.username, vb.password


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    login_test()
    upload_test()
    add_cover_test()
    metadata_test()
    collection_test()
    inventory_test()
    delete_test()
    inventory_test()
