#!/usr/bin/env python3


import logging
import json
import time
import tomllib
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import warnings


import requests
import curl_cffi
from varboxes import VarBox
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.options import BaseOptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


class PytolinoException(Exception):
    pass


class ExpirationError(PytolinoException):
    pass


SERVERS_SETTINGS_FN = 'servers_settings.toml'
SERVERS_SETTINGS_FP = Path(__file__).parent / SERVERS_SETTINGS_FN
servers_settings = tomllib.loads(SERVERS_SETTINGS_FP.read_text())
PARTNERS = servers_settings.keys()

COMMON_SETTINGS_FN = 'common_settings.toml'
COMMON_SETTINGS_FP = Path(__file__).parent / COMMON_SETTINGS_FN
common_settings = tomllib.loads(COMMON_SETTINGS_FP.read_text())
client_id = common_settings['client_id']
scope = common_settings['scope']
redirect_uri = common_settings['redirect_uri']
additional_request_parameters = common_settings[
'additional_request_parameters']
devices_url = common_settings['devices_url']
devices_list_headers = common_settings['headers']['devices_list']
token_headers = common_settings['headers']['token']

USERAGENT = 'User-Agent'
ACCESS_TOKEN = 'access_token'
REFRESH_TOKEN = 'refresh_token'
EXPIRES_IN = 'expires_in'
REFRESH_EXPIRES_IN = 'refresh_expires_in'
AUTH_TOKEN = 'auth_token'
RESELLER_ID = 'reseller_id'
DEVICE_LIST_REQUEST = 'deviceListRequest'
ACCOUNTS = 'accounts'
T_AUTH_TOKEN = 't_auth_token'
DEVICE_LIST_RESPONSE = 'deviceListResponse'
DEVICES = 'devices'
DEVICE_LAST_USAGE = 'deviceLastUsage'
DEVICE_ID = 'deviceId'
HARDWARE_ID = 'hardware_id'
DELIVERABLE_ID = 'deliverableId'


def main():
    print(additional_request_parameters)
    for partner in PARTNERS:
        print(partner)
        for key, val in servers_settings[partner].items():
            print(key, val)


class Client(object):

    """create a client to communicate with a tolino partner (login, etc..)"""

    _IMPERSONATE = 'chrome'

    def _log_request(self, rsp: requests.Response, data=None):
        if rsp.ok:
            log = logging.debug
        else:
            log = logging.error
        log('=====request=======')
        log(rsp.url)
        log(rsp.request.method)
        log('data:')
        log(data)
        log('response:')
        log(rsp)
        log('response text:')
        log(rsp.text)
        log('request header:')
        log(rsp.request.headers)
        log('response header:')
        log(rsp.headers)
        log('===================')

        if not rsp.ok:
            raise PytolinoException('host response not ok')


    def store_token(
                    account_name,
                    refresh_token: str,
                    expires_in: int,
                    refresh_expires_in: int,
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
        vb.refresh_expires_in = refresh_expires_in
        vb.timestamp = time.time()
        vb.access_token = access_token

    def _store_current_token(self, username: str):
        """store the token with attribute of self

        """
        vb = VarBox(app_name=f'{self._server_name}.{username}')
        vb.refresh_token = self._refresh_token
        vb.access_token = self._access_token
        vb.hardware_id = self._hardware_id
        vb.access_expiration_time = self._access_expiration_time
        vb.refresh_expiration_time = self._refresh_expiration_time

    def _retrieve_last_token(self, username):
        """retrieve token that was stored with this username

        """
        vb = VarBox(app_name=f'{self._server_name}.{username}')
        if not hasattr(vb, 'refresh_token'):
            raise PytolinoException(
                    'there was no refresh token stored for that name')
        self._refresh_token = vb.refresh_token
        self._access_token = vb.access_token
        self._hardware_id = vb.hardware_id
        self._access_expiration_time = vb.access_expiration_time
        self._refresh_expiration_time = vb.refresh_expiration_time

    def raise_for_access_expiration(self) -> bool:
        """verify if access token is expired"""
        if self._access_expiration_time < time.time():
            raise ExpirationError('access token is expired')

    def raise_for_refresh_expiration(self) -> bool:
        """verify if refresh token is expired"""
        now = time.time()
        if self._refresh_expiration_time < now:
            # msg = f'refresh expiration is at {self._refresh_expiration_time}'
            # logging.error(msg)
            # msg = f'now is {now}'
            # logging.error(msg)
            raise ExpirationError('refresh token is expired')

    @property
    def refresh_token(self) -> str:
        """refresh token to get new access token"""
        return self._refresh_token

    @property
    def hardware_id(self) -> str:
        """hardware id that is sent in request payloads"""
        return self._hardware_id

    @property
    def expires_in(self) -> int:
        """expiration time in second of access token"""
        return self._expires_in

    @property
    def refresh_expires_in(self) -> int:
        """expiration time (s) of refresh token"""
        return self._refresh_expires_in

    @property
    def access_token(self) -> str:
        """value of access token"""
        return self._access_token

    def __init__(self, server_name='orellfuessli'):

        if server_name not in servers_settings:
            raise PytolinoException(
                    f'the partner {server_name} was not found.'
                    f'please choose one of the list: {PARTNERS}')

        self._server_name = server_name
        self._access_token = None
        self._refresh_token = None
        self._expires_in = None
        self._refresh_expires_in = None
        self._hardware_id = None
        self._access_expiration_time = 0
        self._refresh_expiration_time = 0
        self._user_agent = None

        self._server_settings = servers_settings[server_name]
        self._shadow_host_id = self._server_settings['shadow_host_id']
        self._username_field_id = self._server_settings['username_field_id']
        self._username_field_id = self._server_settings['username_field_id']
        self._cookie_deny_css = self._server_settings['cookie_deny_all_css']
        self._username_field_id = self._server_settings['username_field_id']
        self._password_field_id = self._server_settings['password_field_id']
        self._submit_css = self._server_settings['submit_button_css']
        self._login_url = self._server_settings['login_url']
        self._auth_url = self._server_settings['auth_url']
        self._token_url = self._server_settings['token_url']
        self._partner_id = self._server_settings['partner_id']
        self._upload_url = self._server_settings['upload_url']
        self._delete_url = self._server_settings['delete_url']
        self._cover_url = self._server_settings['cover_url']

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
        access_expiration_time = vb.timestamp + vb.expires_in
        refresh_expiration_time = vb.timestamp + vb.refresh_expires_in
        self._refresh_token = vb.refresh_token
        self._hardware_id = vb.hardware_id
        self._access_token = vb.access_token
        self._expires_in = vb.expires_in
        self._refresh_expires_in = vb.refresh_expires_in
        self._access_expiration_time = access_expiration_time
        self._refresh_expiration_time = refresh_expiration_time

    def get_new_token(self, account_name=None):
        """look at the store token, and get a new access and refresh tokens.

        :account_name: TODO
        :returns: TODO

        """
        if account_name is not None:
            self.retrieve_token(account_name)
        self.raise_for_refresh_expiration()

        headers = {
                # 'Accept': "*/*",
                # 'Accept-Encoding': 'gzip, deflate, br, zstd',
                # 'Accept-Language': 'fr,fr-FR;q=0.9,en-US;q=0.8,en;q=0.7',
                # 'Connection': 'keep-alive',
                # 'Content-Type': "application/x-www-form-urlencoded",
                # 'Host': 'www.orellfuessli.ch',
                # 'Origin': 'https://webreader.mytolino.com',
                # 'Priority': 'u=4',
                'Referer': 'https://webreader.mytolino.com/',
                # 'Sec-Fetch-Dest': 'empty',
                # 'Sec-Fetch-Mode': 'cors',
                # 'Sec-Fetch-Site': 'cross-site',
                # 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
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
                impersonate=self._IMPERSONATE,
                )
        self._log_request(host_response, data=payload)
        j = host_response.json()
        self._access_token = j['access_token']
        self._refresh_token = j['refresh_token']
        self._expires_in = int(j['expires_in'])
        self._refresh_expires_in = int(j['refresh_expires_in'])
        now = time.time()
        self._access_expiration_time = now + self._expires_in
        self._refresh_expiration_time = now + self._refresh_expires_in
        if account_name is not None:
            Client.store_token(
                    account_name,
                    self.refresh_token,
                    self._expires_in,
                    self._refresh_expires_in,
                    self.hardware_id,
                    access_token=self._access_token,
                    )
        logging.info('got a new access token!')
        logging.info(
                f'access will expire in {self._expires_in}s')
        logging.info(
                f'refresh will expire in {self._refresh_expires_in}s')

    def _get_login_cookies(self, username, password):

        timeout = 2
        driver = Driver(uc=True, headless=False)
        driver.implicitly_wait(timeout)
        url = self._login_url
        driver.get(url)

        # deny cookies
        shadow_host_id = self._shadow_host_id
        shadow_host = driver.find_element(By.ID, shadow_host_id)
        shadow_root = shadow_host.shadow_root
        css = self._cookie_deny_css
        wait = WebDriverWait(shadow_root, timeout)
        deny_button = wait.until(
                expected_conditions.element_to_be_clickable(
                    (By.CSS_SELECTOR, css)))
        deny_button.click()

        # fill credentials and submit
        username_field_id = self._username_field_id
        username_field = driver.find_element(
                By.ID, username_field_id,
                )
        password_field_id = self._password_field_id
        password_field = driver.find_element(
                By.ID, password_field_id,
                )
        css = self._submit_css
        submit_button = driver.find_element(
                By.CSS_SELECTOR, css,
                )
        username_field.send_keys(username)
        password_field.send_keys(password)
        wait = WebDriverWait(driver, timeout=2)
        wait.until(
                expected_conditions.element_to_be_clickable(
                    submit_button))
        submit_button.click()

        # get cookies
        cookies = driver.get_cookies()
        user_agent = driver.get_user_agent()
        self._user_agent = user_agent
        driver.quit()
        for cookie in cookies:
            self._session_cffi.cookies.set(cookie['name'], cookie['value'])
            self._session.cookies.set(cookie['name'], cookie['value'])

    def _get_auth_code(self):

        url = self._auth_url
        LOCATION = 'location'
        CODE = 'code'

        params = dict(
                client_id=client_id,
                response_type=CODE,
                scope=scope,
                redirect_uri=redirect_uri,
                )
        params.update(additional_request_parameters)

        host_response = self._session_cffi.get(
                url,
                params=params,
                verify=True,
                allow_redirects=False,
                impersonate=self._IMPERSONATE,
                )
        self._log_request(host_response, params)
        headers = host_response.headers
        try:
            location_url = headers[LOCATION]
        except KeyError:
            raise PytolinoException(
                    'failed to get auth code, '
                    'response headers has no location key')
        else:
            query_str = urlparse(location_url).query
            location_parameters = parse_qs(query_str)
            auth_code = location_parameters[CODE][0]
        return auth_code

    def _add_user_agent(self, headers: dict)->dict:
        if self._user_agent:
            user_agent = self._user_agent
            headers[USERAGENT] = user_agent
        return headers

    def _get_token(self, auth_code: str):

        AUTHORIZATION_CODE = 'authorization_code'

        data = dict(
                client_id=client_id,
                grant_type=AUTHORIZATION_CODE,
                code=auth_code,
                scope=scope,
                redirect_uri=redirect_uri,
                )
        data.update(additional_request_parameters)

        headers = token_headers
        url = self._token_url
        host_response = self._session_cffi.post(
                url,
                data=data,
                verify=True,
                allow_redirects=False,
                headers=headers,
                impersonate=self._IMPERSONATE,
                )
        self._log_request(host_response, data)
        data_rsp = host_response.json()
        self._access_token = data_rsp[ACCESS_TOKEN]
        self._refresh_token = data_rsp[REFRESH_TOKEN]
        self._expires_in = data_rsp[EXPIRES_IN]
        self._refresh_expires_in = data_rsp[REFRESH_EXPIRES_IN]
        now = time.time()
        self._access_expiration_time = now + self._expires_in
        self._refresh_expiration_time = now + self._refresh_expires_in

    def _get_hardware_id(self):
        url = devices_url
        account = {
                AUTH_TOKEN: self._access_token,
                RESELLER_ID: self._partner_id,
                }
        accounts = [account]
        data_dict = {
                DEVICE_LIST_REQUEST: {
                    ACCOUNTS: accounts
                    }
                }
        data = json.dumps(data_dict)
        headers = devices_list_headers
        headers[T_AUTH_TOKEN] = self._access_token
        headers[RESELLER_ID] = self._partner_id
        host_response = self._session.post(
                url,
                data=data,
                headers=headers,
                )
        self._log_request(host_response, data)
        j = host_response.json()
        devices =  j[DEVICE_LIST_RESPONSE][DEVICES]
        devices.sort(key=lambda el:el[DEVICE_LAST_USAGE])
        my_dev = devices[-1]
        hardware_id = my_dev[DEVICE_ID]
        self._hardware_id = hardware_id

    def login(self, username, password, force_new_token=False):
        """login to the partner and get access token.

        """
        if not force_new_token:
            try:
                self._retrieve_last_token(username)
                try:
                    self.raise_for_access_expiration()
                except ExpirationError:
                    try:
                        self.raise_for_refresh_expiration()
                    except ExpirationError:
                        logged_in = False
                    else:
                        self.get_new_token()
                        logged_in = True
                else:
                    self.get_new_token()
                    logged_in = True
            except PytolinoException:
                logged_in = False
        else:
            logged_in = False

        if not logged_in:
            self._get_login_cookies(username, password)
            auth_code = self._get_auth_code()
            self._get_token(auth_code)
            self._get_hardware_id()
        self._store_current_token(username)

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

    def upload(
            self,
            file_path: Path or str,
            name=None,
            ):
        """upload an ebook to your cloud

        :file_path: str path to the ebook to upload
        :name: str name of book if different from filename
        :extension: epub or pdf, if not in filename
        :returns: epub_id on the server

        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            warnings.warn(
                    'file_path arg should better be a Path object',
                    DeprecationWarning,)

        if name is None:
            name = file_path.name
        extension = file_path.suffix

        epubmime = 'application/epub+zip'
        pdfmime = 'application/pdf'
        mime = epubmime if extension == '.epub' else pdfmime

        url = self._upload_url
        headers={
            T_AUTH_TOKEN: self.access_token,
            HARDWARE_ID: self.hardware_id,
            RESELLER_ID: self._partner_id,
            }
        with open(file_path, 'rb') as ebook_file:
            files = [('file', (name, open(file_path, 'rb'), mime))]
            host_response = self._session.post(
                    url,
                    files=files,
                    headers=headers,
                    )
        self._log_request(host_response, files)

        try:
            j = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException('file upload failed. answer not json')
        else:
            try:
                return j['metadata']['deliverableId']
            except KeyError:
                raise PytolinoException(
                        'file upload failed.'
                        'no metadata or deliverableId in response')

    def delete_ebook(self, ebook_id):
        """delete an ebook present on your cloud

        :ebook_id: id of the ebook to delete.
        :returns: None

        """
        url = self._delete_url
        params = {DELIVERABLE_ID: ebook_id}
        headers={
            T_AUTH_TOKEN: self.access_token,
            HARDWARE_ID: self.hardware_id,
            RESELLER_ID: self._partner_id,
            }
        host_response = self._session.get(
                url,
                params=params,
                headers=headers,
                )
        self._log_request(host_response, params)

    def add_cover(self, book_id, filepath: Path or str):
        """upload a a cover to a book on the cloud

        :book_id: id of the book on the serveer
        :filepath: path to the cover file
        :file_ext: png, jpg or jpeg. only necessary if the
        filepath has no extension

        """

        if isinstance(filepath, str):
            filepath = Path(filepath)
            warnings.warn(
                    'file_path arg should better be a Path object',
                    DeprecationWarning,)

        ext = filepath.suffix

        mime = {
                '.png': 'image/png',
                '.jpeg': 'image/jpeg',
                '.jpg': 'image/jpeg'
                }.get(ext.lower(), 'application/jpeg')

        url = self._cover_url
        host_response = self._session.post(
                url,
                files=[('file', ('1092560016', open(filepath, 'rb'), mime))],
                data={'deliverableId': book_id},
                headers={
                    't_auth_token': self._access_token,
                    'hardware_id': self.hardware_id,
                    'reseller_id': self._server_settings['partner_id'],
                    },
                )
        self._log_request(host_response)



if __name__ == '__main__':
    main()
