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


from pytolino.tolino_cloud import Client, PytolinoException


TEST_EPUB = 'basic-v3plus2.epub'


# logging.basicConfig(level=logging.INFO)


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
        username = input('username')
        password = getpass.getpass()
    return username, password


def client_method_tests():

    client = Client('www.orellfuessli.ch')
    username, password = get_test_credentials(client.server_name)
    try:
        reuse_access_token(client)
        client.login(username, password)
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
    # fp = Path(__file__).parent / 'access_token'
    # access_token = fp.read_text()
    access_token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJvVjZNMEZTbzd3V08yYVdPV2hOWElTYkVxQ3VScGQ5ak43SHRFTmNMSlBJIn0.eyJleHAiOjE3NzAyNDMwMjUsImlhdCI6MTc3MDIzOTQyNSwianRpIjoiNjVjNjI1OGItMzNhNy00Yjk2LWI4NjQtZGJmOGFmNmVlZTdlIiwiaXNzIjoiaHR0cHM6Ly93d3cub3JlbGxmdWVzc2xpLmNoL2tleWNsb2FrL3JlYWxtcy8zNyIsInN1YiI6IjUzOTExMzIyIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoid2VicmVhZGVyIiwic2lkIjoiYzU1OGM3MjAtOWYxMi00MjBlLWFkMTgtMTU5NmRjMmEwNGMyIiwic2NvcGUiOiJTQ09QRV9CT1NIIiwiZXhwaXJlcyI6IjE3NzAyNDMwMjUwMDAiLCJ4X2J1Y2hkZS51c2VyX2lkIjoiNTM5MTEzMjIifQ.eth8KcC8p5YiDdwvLtQamZN8o_JSidD8ctXhlmg5mngA_hqarbtLGx41_gguZooWSWt93jeX0TT1z9M0CZHnmfuSuWxF3eUgK4A9thYxBXeA-n4eMQVxVS5EHJ_lyHC57P9MrKpS9tGB9DR2Dsrr-z5LbbMOQt3RGfTohpnWBAC9DvhZZD68s9yDhOoTQoYVQTUJkB1Vqt8UVWRuVLpHdxchwVTewzgHLaR5PLX-VKBIAJjguvxfug5RXclyg0gfJ_is17DNE6a5RXzxayt5nRx40J6Ie5ut7qbp-vOhPO3iAyT9g3MAk8XO9Eb3S3nI0HUbrJuyRHWQ8QXUuEbcQQ'
    refresh_token = 'eyJhbGciOiJIUzUxMiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJkMmExN2EyNS01YmJkLTRiMTMtOTgzMi04ZGExMWFjNmU2ZTQifQ.eyJleHAiOjE3NzAyNDU5MjAsImlhdCI6MTc3MDI0MjMyMCwianRpIjoiOGU3MWYxMzItMzkwZS00NzY1LTgyMDMtYTA4NjJjNzA4N2IyIiwiaXNzIjoiaHR0cHM6Ly93d3cub3JlbGxmdWVzc2xpLmNoL2tleWNsb2FrL3JlYWxtcy8zNyIsImF1ZCI6Imh0dHBzOi8vd3d3Lm9yZWxsZnVlc3NsaS5jaC9rZXljbG9hay9yZWFsbXMvMzciLCJzdWIiOiI1MzkxMTMyMiIsInR5cCI6IlJlZnJlc2giLCJhenAiOiJ3ZWJyZWFkZXIiLCJzaWQiOiIzNmE1NDM4NS01ODkxLTQ3MjEtYmVlNS01NTRlYjAxN2QwYWIiLCJzY29wZSI6IlNDT1BFX0JPU0giLCJyZXVzZV9pZCI6IjhkZDUxNzZjLTIxNDktNDU3Ny1hYzNjLTU5ZmIzM2ZkMzNhYiJ9.EYFxmEzfcMPsSpw8tTkC7fY8i1WNXJHcWnP7XsxdTdjbiaUObsM1ifWpCZOfiGOtyXJAjPYjolZ-rK7AbuI2LQ'
    # client.access_token = access_token
    client.refresh_token = refresh_token
    # fp = Path(__file__).parent / 'hw_id'
    # hw_id = fp.open().read()
    hw_id = '654b7d6f-f4ff-4714-9b79-154caaad0534'
    client.hardware_id = hw_id


def upload_test():

    epub_fp = Path(__file__).parent / TEST_EPUB

    client = Client('www.orellfuessli.ch')
    reuse_access_token(client)
    # return

    # username, password = get_test_credentials(client.server_name)
    # client.login(username, password)
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
    reuse_access_token(client)
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


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    # del_test_credentials('www.buecher.de')
    # cred = get_test_credentials('www.buecher.de')
    # print(cred)
    # register_test()
    # unregister_test()
    client_method_tests()
    # upload_test()
    # delete_test()
    # add_cover_test()
    # metadata_test()
    # inventory_test()
