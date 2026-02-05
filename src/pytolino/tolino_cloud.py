#!/usr/bin/env python3


import logging
import json
import time
import tomllib
from pathlib import Path


import requests
import curl_cffi
from varboxes import VarBox


class PytolinoException(Exception):
    pass


class ExpirationError(PytolinoException):
    pass


SERVERS_SETTINGS_FN = 'servers_settings.toml'
SERVERS_SETTINGS_FP = Path(__file__).parent / SERVERS_SETTINGS_FN
servers_settings = tomllib.loads(SERVERS_SETTINGS_FP.read_text())
PARTNERS = servers_settings.keys()


def main():
    for partner in PARTNERS:
        print(partner)
        for key, val in servers_settings[partner].items():
            print(key, val)


class Client(object):

    """create a client to communicate with a tolino partner (login, etc..)"""

    def store_token(
                    account_name,
                    refresh_token: str,
                    expires_in: int,
                    hardward_id: str,
                    access_token='',
                    ):
        """after one has connected in a browser,
        one can store the token for the app.

        :account_name: internal name for reference
        :refresh_token: given by server after a token POST request
        :expires_in: time in seconds
        :hardward_id: present in payload for every request to API.

        """
        vb = VarBox('pytolino', app_name=account_name)
        vb.refresh_token = refresh_token
        vb.hardware_id = hardward_id
        vb.expires_in = expires_in
        vb.timestamp = time.time()
        vb.access_token = access_token

    @property
    def refresh_token(self) -> str:
        """refresh token to get new access token"""
        return self._refresh_token

    @property
    def hardware_id(self) -> str:
        """hardware id that is sent in request payloads"""
        return self._hardware_id

    def __init__(self, server_name='orellfuessli'):

        if server_name not in servers_settings:
            raise PytolinoException(
                    f'the partner {server_name} was not found.'
                    f'please choose one of the list: {PARTNERS}')

        self._access_token = None
        self._refresh_token = None
        self._token_expires = None
        self._hardware_id = None

        self._server_settings = servers_settings[server_name]
        self._session = requests.Session()
        self._session_cffi = curl_cffi.Session()
        self._server_name = server_name

    def retrieve_token(
            self,
            account_name,
            ) -> tuple[str, str]:
        """get the token and data that were stored previousely.
        raise error if expired

        :account_name: internal name under which token was stored
        :returns: refresh_token, hardware_id

        """
        vb = VarBox('pytolino', app_name=account_name)
        if not hasattr(vb, 'refresh_token'):
            raise PytolinoException(
                    'there was no refresh token stored for that name')
        now = time.time()
        expiration_time = vb.timestamp + vb.expires_in
        if now > expiration_time:
            raise ExpirationError('the refresh token has expired')
        else:
            self._refresh_token = vb.refresh_token
            self._hardware_id = vb.hardware_id
            self._access_token = vb.access_token

    def get_new_token(self, account_name):
        """look at the store token, and get a new access and refresh tokens.

        :account_name: TODO
        :returns: TODO

        """
        self.retrieve_token(account_name)

        headers = {
                'Referer': 'https://webreader.mytolino.com/',
                }
        payload = {
            'client_id': 'webreader',
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'scope': 'SCOPE_BOSH',
        }
        host_response = self._session_cffi.post(
                self._server_settings['token_url'],
                data=payload,
                verify=True,
                allow_redirects=True,
                headers=headers,
                impersonate='chrome',
                )
        if not host_response.ok:
            msg = str(host_response)
            logging.error('failed to get a new token')
            logging.error(msg)
            raise PytolinoException('failed to get a new token')
        else:
            j = host_response.json()
            self._access_token = j['access_token']
            self._refresh_token = j['refresh_token']
            self._token_expires = int(j['expires_in'])
            Client.store_token(
                    account_name,
                    self.refresh_token,
                    self._token_expires,
                    self.hardware_id,
                    access_token=self._access_token,
                    )
            logging.info('got a new access token!')

    def login(self, username, password, fp=None):
        """login to the partner and get access token.

        """
        msg = 'login does not work anymore because of bot protection'
        'connect manualy (once) and use store_token and retrieve token'
        'methods instead'
        raise NotImplementedError(msg)

    def logout(self):
        """logout from tolino partner host

        """
        raise NotImplementedError('logout is not necessary with tokens')

    def register(self):
        raise NotImplementedError('register is not necessary with tokens')

    def unregister(self, device_id=None):
        raise NotImplementedError('unregister is not necessary with tokens')

    def get_inventory(self):
        """download a list of the books on the cloud and their information
        :returns: list of dict describing the book, with a epubMetaData dict

        """

        host_response = self._session.get(
                self._server_settings['inventory_url'],
                params={'strip': 'true'},
                headers={
                    't_auth_token': self._access_token,
                    'hardware_id': self._hardware_id,
                    'reseller_id': self._server_settings['partner_id'],
                    }
                )

        if not host_response.ok:
            raise PytolinoException(
                    f'inventory request failed {host_response}')

        try:
            j = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException(
                    'inventory list request failed because of json error.'
                    )
        else:
            try:
                publication_inventory = j['PublicationInventory']
                uploaded_ebooks = publication_inventory['edata']
                purchased_ebook = publication_inventory['ebook']
            except KeyError:
                raise PytolinoException(
                        'inventory list request failed because',
                        'of key error in json.',
                        )
            else:
                inventory = uploaded_ebooks + purchased_ebook
                return inventory

    def add_to_collection(self, book_id, collection_name):
        """add a book to a collection on the cloud

        :book_id: identify the book on the cloud
        :collection_name: str name

        """

        payload = {
                "revision": None,
                "patches": [{
                    "op": "add",
                    "value": {
                        "modified": round(time.time() * 1000),
                        "name": collection_name,
                        "category": "collection",
                    },
                    "path": f"/publications/{book_id}/tags"
                    }]
                }

        host_response = self._session.patch(
                self._server_settings['sync_data_url'],
                data=json.dumps(payload),
                headers={
                    'content-type': 'application/json',
                    't_auth_token': self._access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self._server_settings['partner_id'],
                    'client_type': 'TOLINO_WEBREADER',
                    }
                )

        if not host_response.ok:
            raise PytolinoException(
                    f'collection add failed {host_response}')

    def upload_metadata(self, book_id, **new_metadata):
        """upload some metadata to a specific book on the cloud

        :book_id: ref on the cloud of the book
        :**meta_data: dict of metadata than can be changed

        """

        url = self._server_settings['meta_url'] + f'/?deliverableId={book_id}'
        host_response = self._session.get(
                url,
                headers={
                    't_auth_token': self._access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self._server_settings['partner_id'],
                  }
                )

        book = host_response.json()
        if not host_response.ok:
            raise PytolinoException(f'metadata upload failed {host_response}')

        for key, value in new_metadata.items():
            book['metadata'][key] = value

        payload = {
                'uploadMetaData': book['metadata']
                }

        host_response = self._session.put(
                url,
                data=json.dumps(payload),
                headers={
                    'content-type': 'application/json',
                    't_auth_token': self._access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self._server_settings['partner_id'],
                    }
                )

        if not host_response.ok:
            raise PytolinoException(f'metadata upload failed {host_response}')

    def upload(self, file_path, name=None, extension=None):
        """upload an ebook to your cloud

        :file_path: str path to the ebook to upload
        :name: str name of book if different from filename
        :extension: epub or pdf, if not in filename
        :returns: epub_id on the server

        """

        if name is None:
            name = file_path.split('/')[-1]
        if extension is None:
            extension = file_path.split('.')[-1]

        mime = {
                'pdf': 'application/pdf',
                'epub': 'application/epub+zip',
                }.get(extension.lower(), 'application/pdf')

        host_response = self._session.post(
                self._server_settings['upload_url'],
                files=[(
                    'file',
                    (
                        name,
                        open(file_path, 'rb'),
                        mime,
                        ),
                    )],
                headers={
                    't_auth_token': self._access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self._server_settings['partner_id'],
                    }
                )

        if not host_response.ok:
            raise PytolinoException(f'upload failed {host_response}')

        try:
            j = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException('file upload failed.')
        else:
            try:
                return j['metadata']['deliverableId']
            except KeyError:
                raise PytolinoException('file upload failed.')

    def delete_ebook(self, ebook_id):
        """delete an ebook present on your cloud

        :ebook_id: id of the ebook to delete.
        :returns: None

        """
        host_response = self._session.get(
                self._server_settings['delete_url'],
                params={'deliverableId': ebook_id},
                headers={
                    't_auth_token': self._access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self._server_settings['partner_id'],
                    }
                )

        if not host_response.ok:
            try:
                j = host_response.json()
                raise PytolinoException(
                        f"delete {ebook_id} failed: ",
                        f"{j['ResponseInfo']['message']}"
                        )
            except KeyError:
                raise PytolinoException(
                        f'delete {ebook_id} failed: reason unknown.')

    def add_cover(self, book_id, filepath, file_ext=None):
        """upload a a cover to a book on the cloud

        :book_id: id of the book on the serveer
        :filepath: path to the cover file
        :file_ext: png, jpg or jpeg. only necessary if the
        filepath has no extension

        """

        if file_ext is None:
            ext = filepath.split('.')[-1]

        mime = {
                'png': 'image/png',
                'jpeg': 'image/jpeg',
                'jpg': 'image/jpeg'
                }.get(ext.lower(), 'application/jpeg')

        host_response = self._session.post(
                self._server_settings['cover_url'],
                files=[('file', ('1092560016', open(filepath, 'rb'), mime))],
                data={'deliverableId': book_id},
                headers={
                    't_auth_token': self._access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self._server_settings['partner_id'],
                    },
                )

        if not host_response.ok:
            raise PytolinoException(f'cover upload failed. {host_response}')


if __name__ == '__main__':
    main()
