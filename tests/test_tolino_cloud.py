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


from pytolino.tolino_cloud import Client, PytolinoException


TEST_EPUB = "basic-v3plus2.epub"
# ACCOUNT_NAME = 'real_test_token'
ACCOUNT_NAME = "test_token"
TEST_COVER = "test_cover.png"


class TestClient(unittest.TestCase):
    """all test concerning the Client class."""

    @classmethod
    def setUpClass(cls):
        cls.client = Client("username")

    def test_init_nopartner(self):
        with self.assertRaises(PytolinoException):
            Client(
                server_name="this tolino partner does not exists",
                username="username",
            )


def upload_test():

    print("upload epub...")
    epub_fp = Path(__file__).parent / TEST_EPUB
    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)
    ebook_id = client.upload(epub_fp)
    print(ebook_id)
    vb = VarBox("pytolino")
    vb.ebook_id = ebook_id


def download_test():

    print("download epub...")
    vb = VarBox("pytolino")
    # ebook_id = vb.ebook_id
    # ebook_id = vb.identifier
    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)
    for ebook_id in [vb.deliverable_id,m vb.identifier]:
        try:
            epub_fp, cover_fp, metadata = client.download(ebook_id)
        except NotImplementedError as e:
            print(e)
        except PytolinoException as e:
            print(e)
        else:
            print(metadata)
            print(f"check epub at {epub_fp} and cover at {cover_fp}")


def collection_test():
    print("add to a collection last epub")
    vb = VarBox("pytolino")
    ebook_id = vb.ebook_id

    username, password = get_test_credentials()
    client = Client(username)
    try:
        client.login(password)
    except PytolinoException as e:
        print(e)
    else:
        try:
            print("add test_coll_2...")
            revision, patch_rev, patch = client.add_to_collection(
                ebook_id, "test_coll_2"
            )
            print("rsp: ", patch["op"], patch["value"]["name"])
            print("rm test_coll_1")
            revision, patch_rev, patch = client.rm_book_from_collection(
                ebook_id, "test_coll_1"
            )
            print("rsp: ", patch["op"], patch["value"]["name"])

        except PytolinoException as e:
            print(e)
        else:
            pass
            # print(revision)
            # print(patch_rev)
            # print(patch)


def mark_finished_test():
    print("mark finish test")
    vb = VarBox("pytolino")
    ebook_id = vb.ebook_id

    username, password = get_test_credentials()
    client = Client(username)
    try:
        client.login(password)
    except PytolinoException as e:
        print(e)
    else:
        try:
            revision, patch_rev, patch = client.mark_book_as_finished(ebook_id)
        except PytolinoException as e:
            print(e)
        else:
            print(revision)
            print(patch_rev)
            print(patch)

def mark_not_finished_test():
    print("mark not finish test")
    vb = VarBox("pytolino")
    ebook_id = vb.ebook_id

    username, password = get_test_credentials()
    client = Client(username)
    try:
        client.login(password)
    except PytolinoException as e:
        print(e)
    else:
        try:
            revision, patch_rev, patch = client.mark_book_as_not_finished(ebook_id)
        except PytolinoException as e:
            print(e)
        else:
            print(revision)
            print(patch_rev)
            print(patch)


def sync_test():
    print("sync test to get revision")
    vb = VarBox("pytolino")
    ebook_id = vb.ebook_id

    username, password = get_test_credentials()
    client = Client(username)
    try:
        client.login(password)
    except PytolinoException as e:
        print(e)
    else:
        try:
            revision, patches = client.get_sync_data()
        except PytolinoException as e:
            print(e)
        else:
            # print(revision, patches)
            for rev, patch in patches.items():
                print(patch["op"])
                for key, value in patch["value"].items():
                    if key != "revision":
                        print(key, value)


def rm_collection_test():
    print("rm test book from test_coll collection...")
    vb = VarBox("pytolino")
    ebook_id = vb.ebook_id

    username, password = get_test_credentials()
    client = Client(username)

    try:
        client.login(password)
    except PytolinoException as e:
        print(e)
    else:
        try:
            client.rm_book_from_collection(ebook_id, "test_coll")
        except PytolinoException as e:
            print(e)
        else:
            print("done")


def delete_test():

    print("delete last epub")
    vb = VarBox("pytolino")
    ebook_id = vb.ebook_id

    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)
    client.delete_ebook(ebook_id)


def inventory_test():

    print("get inventory")
    vb = VarBox("pytolino")
    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)
    inventory = client.get_inventory()
    if inventory:
        for item in inventory:
            metadata = item["epubMetaData"]
            print(metadata["title"])
            # print(item.keys())
            # print(item["publicationId"])
            # print(item["deliverableId"])
            # print(metadata["identifier"])
            if item["publicationId"] is None:
                identifier = metadata["identifier"]
                print(identifier)
                vb.identifier = identifier
            else:
                deliverable_id = item["deliverableId"]
                vb.deliverable_id = deliverable_id
    else:
        print("empty")


def metadata_test():

    print("update metadata")
    metadata = dict(
        title="mytitle",
        isbn="myisbn",
        language="mylanguage",
        author="myauthor",
        publisher="mypublisher",
        issued=time.time(),
    )
    vb = VarBox("pytolino")
    ebook_id = vb.ebook_id
    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)

    client.upload_metadata(ebook_id, **metadata)

    inventory = client.get_inventory()
    book = [
        el for el in inventory if el["epubMetaData"]["identifier"] == ebook_id
    ][0]
    online_metadata = book["epubMetaData"]
    for key in metadata:
        print(key, online_metadata[key])


def add_cover_test():

    print("add cover")

    cover_fp = Path(__file__).parent / TEST_COVER

    vb = VarBox("pytolino")
    ebook_id = vb.ebook_id

    username, password = get_test_credentials()
    client = Client(username)
    client.login(password)
    client.add_cover(ebook_id, cover_fp)


def login_test():
    username, password = get_test_credentials()
    client = Client(username=username)
    expiration = client.access_expiration_time
    print("access token expiration time:")
    print(datetime.datetime.fromtimestamp(expiration))
    print("login...")
    try:
        client.login(password)
    except PytolinoException as e:
        print(e)
    else:
        client = Client(username=username)
        expiration = client.access_expiration_time
        print("access token new expiration time:")
        print(datetime.datetime.fromtimestamp(expiration))


def import_login_test():
    username, password = get_test_credentials()
    client = Client(username=username)
    print(
        "please login manually and use inspector tool to find refresh token"
        " in a token request"
    )
    refresh_token = input("refresh login: ")
    print(
        "find the hardware id in the request header "
        "of a patch request for example"
    )
    hardware_id = input("hardware id: ")
    client.import_token(refresh_token, hardware_id)


def get_test_credentials():
    vb = VarBox("pytolino", "test_credentials")
    if not hasattr(vb, "username"):
        username = input("username:\n")
        password = input("password:\n")
        vb.username = username
        vb.password = password
    return vb.username, vb.password


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # login_test()
    # mark_finished_test()
    # sync_test()
    # mark_not_finished_test()
    # sync_test()
    # upload_test()
    # download_test()
    # add_cover_test()
    # metadata_test()
    # collection_test()
    # rm_collection_test()
    inventory_test()
    # delete_test()
    # inventory_test()
    # import_login_test()
