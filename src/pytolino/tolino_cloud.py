#!/usr/bin/env python3


import os
import configparser
import platform
import logging
from urllib.parse import urlparse, parse_qs
from urllib3.util import Retry
import json
import time
import tomllib


import requests
from requests.adapters import HTTPAdapter
import mechanize
import curl_cffi
from varboxes import VarBox


class PytolinoException(Exception):
    pass


class ExpirationError(PytolinoException):
    pass


SERVERS_SETTINGS_FN = 'servers_settings.ini'
SERVERS_SETTINGS_FILE_PATH = os.path.join(
        os.path.dirname(__file__),
        SERVERS_SETTINGS_FN,
        )
servers_settings = configparser.ConfigParser()
servers_settings.read(SERVERS_SETTINGS_FILE_PATH)

PARTNERS = servers_settings.sections()
TOTAL_RETRY = 5
STATUS_FORCELIST = [404]


def main():
    print(SERVERS_SETTINGS_FILE_PATH)
    print(servers_settings.sections())


class Client(object):

    """create a client to communicate with a tolino partner (login, etc..)"""

    def _log_requests(self, host_response, error: True or None=None):
        if host_response.status_code >= 400 or error is True:
            logger = logging.error
        else:
            logger = logging.debug
        logger('log request')
        logger('---------------- HTTP response (requests)----------')
        logger(f'status code: {host_response.status_code}')
        logger(f'cookies: {host_response.cookies}')
        logger(f'headers: {host_response.headers}')
        try:
            j = host_response.json()
            logger(f'json: {j}')
        except requests.JSONDecodeError:
            logger(f'text: {host_response.text}')
        logger('-------------------------------------------------------')

        try:
            host_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise PytolinoException
        except requests.exceptions.RequestException as e:
            raise PytolinoException

    def _log_mechanize(self, host_response):
        logging.debug('-------------- HTTP response (mechanize)--------------')
        logging.debug(f'status code: {host_response.code}')
        logging.debug(f'headers: {host_response.info()}')
        logging.debug('-------------------------------------------------------')
        if host_response.code >= 400:
            logging.error('-------------- HTTP response (mechanize)----------')
            logging.error(f'status code: {host_response.code}')
            logging.error(f'headers: {host_response.info()}')
            logging.error('--------------------------------------------------')
            raise PytolinoException('http error')

    def _hardware_id():

        os_id = {
            'Windows': '1',
            'Darwin': '2',
            'Linux': '3'
            }.get(platform.system(), 'x')

        engine_id = 'x'
        browser_id = 'xx'
        version_id = '00'
        fingerprint = 'ABCDEFGHIJKLMNOPQR'
        return (
                os_id +
                engine_id +
                browser_id +
                fingerprint[0:1] +
                '-' +
                version_id +
                fingerprint[1:4] +
                '-' +
                fingerprint[4:9] +
                '-' +
                fingerprint[9:14] +
                '-' +
                fingerprint[14:18] +
                'h'
                )

    hardware_id = _hardware_id()


    def store_token(
                    account_name,
                    refresh_token: str,
                    expires_in: int,
                    hardward_id: str,
                    ):
        """after one has connected in a browser, one can store the token for the app.

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

    def retrieve_token(
            self,
            account_name,
            )->tuple[str, str]:
        """get the token and data that were stored previousely. raise error if expired

        :account_name: internal name under which token was stored
        :returns: refresh_token, hardware_id

        """
        vb = VarBox('pytolino', app_name=account_name)
        if not hasattr(vb, 'refresh_token'):
            raise PytolinoException('there was no refresh token stored for that name')
        now = time.time()
        expiration_time = vb.timestamp + vb.expires_in
        if now > expiration_time:
            raise ExpirationError('the refresh token has expired')
        else:
            self.refresh_token = vb.refresh_token
            self.hardware_id = vb.hardware_id

    def __init__(self, server_name='www.buecher.de'):

        if server_name not in servers_settings:
            raise PytolinoException(
                    f'the partner {server_name} was not found.'
                    f'please choose one of the list: {PARTNERS}')

        self.access_token = None
        self.refresh_token = None
        self.token_expires = None

        self.server_settings = servers_settings[server_name]
        self.session = requests.Session()
        self.session_cffi = curl_cffi.Session()
        # retry_strategy = Retry(
                # total=TOTAL_RETRY,
                # status_forcelist=STATUS_FORCELIST,
                # backoff_factor=2,
                # allowed_methods=frozenset(['GET', 'POST']))
        # adapter = HTTPAdapter(max_retries=retry_strategy)
        # self.session.mount('http://', adapter)
        # self.session.mount('https://', adapter)
        # self.browser = mechanize.Browser()
        # self.browser.set_handle_robots(False)
        self.server_name = server_name

    def get_new_token(self, account_name):
        """look at the store token, and get a new access and refresh tokens.

        :account_name: TODO
        :returns: TODO

        """
        refresh_token, hardware_id = Client.retrieve_token(account_name)

        headers = {
                'Host': 'www.orellfuessli.ch',
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
                'Accept': "*/*",
                'Accept-Language': 'fr,fr-FR;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': '742',
                'Referer': 'https://webreader.mytolino.com/',
                'Origin': 'https://webreader.mytolino.com',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'Connection': 'keep-alive',
                'Priority': 'u=4',
                }
        payload = {
            'client_id': 'webreader',
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'scope': 'SCOPE_BOSH',
        }
        host_response = self.session_cffi.post(
                self.server_settings['token_url'],
                data=payload,
                verify=True,
                allow_redirects=True,
                headers=headers,
                impersonate='chrome',
                )
        print(host_response)
        try:
            j = host_response.json()
            self.access_token = j['access_token']
            self.refresh_token = j['refresh_token']
            self.token_expires = int(j['expires_in'])
        # except requests.JSONDecodeError:
        except json.decoder.JSONDecodeError:
            raise PytolinoException('oauth access token request failed.')
        else:
            data = dict(
                    refresh_token = self.refresh_token,
                    hardware_id = self.hardware_id,
                    )
            if fp is not None:
                with open(fp.as_posix(), 'wb') as f:
                    tomli_w.dump(data, f)

    def login(self, username, password, fp=None):
        """login to the partner and get access token.

        :username: str
        :password: str
        :returns: None, but raises pytolino exceptions if fail
        """
        logging.info(f'login to {self.server_name}...')
        if fp is not None:
            with open(fp.as_posix(), 'rb') as f:
                data = tomllib.load(f)
            self.refresh_token = data['refresh_token']
            self.hardware_id = data['hardware_id']

        # self.browser.open(self.server_settings['login_url'])
        # self.browser.select_form(id=self.server_settings['form_id'])
        # self.browser[self.server_settings['username_field']] = username
        # self.browser[self.server_settings['password_field']] = password
        # host_response = self.browser.submit()

        # for cookie in self.browser.cookiejar:
            # self.session.cookies.set(cookie.name, cookie.value)

        # logging.debug(self.server_settings['login_cookie'])
        # self._log_mechanize(host_response)
        # if not self.server_settings['login_cookie'] in self.session.cookies:
            # raise PytolinoException(f'login to {self.server_name} failed.')

        # rsp = self.session.get(
                # self.server_settings['login_url'],
                # impersonate='chrome',
                # )
        # print(rsp)
        # headers= {
            # 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0'
        # }
        headers = {
                'Host': 'www.orellfuessli.ch',
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
                'Accept': "*/*",
                'Accept-Language': 'fr,fr-FR;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': '742',
                'Referer': 'https://webreader.mytolino.com/',
                'Origin': 'https://webreader.mytolino.com',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'Connection': 'keep-alive',
                'Priority': 'u=4',
                }
        payload = {
            # 'client_id': self.server_settings['client_id'],
            'client_id': 'webreader',
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'scope': 'SCOPE_BOSH',
        }
        host_response = self.session_cffi.post(
                self.server_settings['token_url'],
                data=payload,
                verify=True,
                allow_redirects=True,
                headers=headers,
                impersonate='chrome',
                )
        print(host_response)
        try:
            j = host_response.json()
            self.access_token = j['access_token']
            self.refresh_token = j['refresh_token']
            self.token_expires = int(j['expires_in'])
        # except requests.JSONDecodeError:
        except json.decoder.JSONDecodeError:
            raise PytolinoException('oauth access token request failed.')
        else:
            data = dict(
                    refresh_token = self.refresh_token,
                    hardware_id = self.hardware_id,
                    )
            if fp is not None:
                with open(fp.as_posix(), 'wb') as f:
                    tomli_w.dump(data, f)

        # auth_code = ""

        # params = {
            # 'client_id': self.server_settings['client_id'],
            # 'response_type': 'code',
            # 'scope': self.server_settings['scope'],
            # 'redirect_uri': self.server_settings['reader_url']
        # }
        # if 'login_form_url' in self.server_settings:
            # params['x_buchde.skin_id'] = self.server_settings[
                    # 'x_buchde.skin_id']
            # params['x_buchde.mandant_id'] = self.server_settings[
                    # 'x_buchde.mandant_id']
        # host_response = self.session.get(
                # self.server_settings['auth_url'],
                # params=params,
                # verify=True,
                # allow_redirects=False,
                # )

        # self._log_requests(host_response)

        # try:
            # params = parse_qs(urlparse(
                # host_response.headers['Location']
                # ).query)
            # auth_code = params['code'][0]
        # except KeyError:
            # self._log_requests(host_response, error=True)
            # raise PytolinoException('oauth code request failed.')

        # # Fetch OAUTH access token
        # host_response = self.session.post(
                # self.server_settings['token_url'],
                # data={
                    # 'client_id': self.server_settings['client_id'],
                    # 'grant_type': 'authorization_code',
                    # 'code': auth_code,
                    # 'scope': self.server_settings['scope'],
                    # 'redirect_uri': self.server_settings['reader_url']
                    # },
                # verify=True,
                # allow_redirects=False,
                # )
        # self._log_requests(host_response)


    def logout(self):
        """logout from tolino partner host

        """
        return
        if 'revoke_url' in self.server_settings:
            host_response = self.session.post(
                    self.server_settings['revoke_url'],
                    data={
                        'client_id': self.server_settings['client_id'],
                        'token_type': 'refresh_token',
                        'token': self.refresh_token,
                        }
                    )
            self._log_requests(host_response)
            if host_response.status_code != 200:
                raise PytolinoException('logout failed.')
        else:
            host_response = self.session.post(
                    self.server_settings['logout_url'],
                    )
            self._log_requests(host_response)
            if host_response.status_code != 200:
                raise PytolinoException('logout failed.')

    def register(self):
        """register your device. Needs to done only once! necessary to
        upload files. you need to login first.

        """
        host_response = self.session.post(
                self.server_settings['register_url'],
                data=json.dumps({'hardware_name': 'tolino sync reader'}),
                headers={
                    'content-type': 'application/json',
                    't_auth_token': self.access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self.server_settings['partner_id'],
                    'client_type': 'TOLINO_WEBREADER',
                    'client_version': '4.4.1',
                    'hardware_type': 'HTML5',
                    }
                )
        self._log_requests(host_response)
        if host_response.status_code != 200:
            raise PytolinoException(f'register {self.hardware_id} failed.')

    def unregister(self, device_id=None):
        """unregister a device from the host partner. If no device is given,
        it is assumed the device in use will be removed

        :device_id: None or str if we want to unregister another device
        :returns: None

        """
        if device_id is None:
            device_id = self.hardware_id

        host_response = self.session.post(
                self.server_settings['unregister_url'],
                data=json.dumps({
                    'deleteDevicesRequest': {
                        'accounts': [{
                            'auth_token': self.access_token,
                            'reseller_id': self.server_settings['partner_id'],
                            }],
                        'devices': [{
                            'device_id': device_id,
                            'reseller_id': self.server_settings['partner_id'],
                            }]
                        }
                    }),
                headers={
                    'content-type': 'application/json',
                    't_auth_token': self.access_token,
                    'reseller_id': self.server_settings['partner_id'],
                    }
                )
        self._log_requests(host_response)
        if host_response.status_code != 200:
            try:
                j = host_response.json()
                raise PytolinoException(
                        f"unregister {device_id} failed: ",
                        f"{j['ResponseInfo']['message']}"
                        )
            except KeyError:
                raise PytolinoException(
                        f'unregister {device_id} failed: reason unknown.')

    def get_inventory(self):
        """download a list of the books on the cloud and their information
        :returns: list of dict describing the book, with a epubMetaData dict

        """

        host_response = self.session.get(
                self.server_settings['inventory_url'],
                params={'strip': 'true'},
                headers={
                    't_auth_token': self.access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self.server_settings['partner_id'],
                    }
                )

        self._log_requests(host_response)
        if host_response.status_code != 200:
            raise PytolinoException('invetory request failed')

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

        host_response = self.session.patch(
                self.server_settings['sync_data_url'],
                data=json.dumps(payload),
                headers={
                    'content-type': 'application/json',
                    't_auth_token': self.access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self.server_settings['partner_id'],
                    'client_type': 'TOLINO_WEBREADER',
                    }
                )
        self._log_requests(host_response)
        if host_response.status_code != 200:
            raise PytolinoException('add to collection failed')

    def upload_metadata(self, book_id, **new_metadata):
        """upload some metadata to a specific book on the cloud

        :book_id: ref on the cloud of the book
        :**meta_data: dict of metadata than can be changed

        """

        url = self.server_settings['meta_url'] + f'/?deliverableId={book_id}'
        host_response = self.session.get(
                url,
                headers={
                    't_auth_token': self.access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self.server_settings['partner_id'],
                  }
                )

        book = host_response.json()
        self._log_requests(host_response)
        if host_response.status_code != 200:
            raise PytolinoException('metadata upload failed')

        for key, value in new_metadata.items():
            book['metadata'][key] = value

        payload = {
                'uploadMetaData': book['metadata']
                }

        host_response = self.session.put(
                url,
                data=json.dumps(payload),
                headers={
                    'content-type': 'application/json',
                    't_auth_token': self.access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self.server_settings['partner_id'],
                    }
                )

        self._log_requests(host_response)
        if host_response.status_code != 200:
            raise PytolinoException('metadata upload failed')

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

        host_response = self.session.post(
                self.server_settings['upload_url'],
                files=[(
                    'file',
                    (
                        name,
                        open(file_path, 'rb'),
                        mime,
                        ),
                    )],
                headers={
                    't_auth_token': self.access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self.server_settings['partner_id'],
                    }
                )
        # self._log_requests(host_response)
        # if host_response.status_code != 200:
            # raise PytolinoException('file upload failed.')
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
        host_response = self.session.get(
                self.server_settings['delete_url'],
                params={'deliverableId': ebook_id},
                headers={
                    't_auth_token': self.access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self.server_settings['partner_id'],
                    }
                )
        self._log_requests(host_response)

        if host_response.status_code != 200:
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

        host_response = self.session.post(
                self.server_settings['cover_url'],
                files=[('file', ('1092560016', open(filepath, 'rb'), mime))],
                data={'deliverableId': book_id},
                headers={
                    't_auth_token': self.access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self.server_settings['partner_id'],
                    },
                )

        self._log_requests(host_response)

        if host_response.status_code != 200:
            raise PytolinoException('cover upload failed.')


if __name__ == '__main__':
    main()
