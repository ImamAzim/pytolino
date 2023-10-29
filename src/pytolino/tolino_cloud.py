#!/usr/bin/env python3


import os
import configparser
import platform
import logging
from urllib.parse import urlparse, parse_qs
import json


import requests
import mechanize


class PytolinoException(Exception):
    pass


SERVERS_SETTINGS_FN = 'servers_settings.ini'
SERVERS_SETTINGS_FILE_PATH = os.path.join(
        os.path.dirname(__file__),
        SERVERS_SETTINGS_FN,
        )
servers_settings = configparser.ConfigParser()
servers_settings.read(SERVERS_SETTINGS_FILE_PATH)


def main():
    print(SERVERS_SETTINGS_FILE_PATH)
    print(servers_settings.sections())


class Client(object):

    """create a client to communicate with a tolino partner (login, etc..)"""

    def _log_requests(self, host_response):
        logging.info('-------------------- HTTP response --------------------')
        logging.info(f'status code: {host_response.status_code}')
        logging.info(f'cookies: {host_response.cookies}')
        logging.info(f'headers: {host_response.headers}')
        try:
            j = host_response.json()
            logging.debug(f'json: {j}')
        except requests.JSONDecodeError:
            logging.debug(f'text: {host_response.text}')
        logging.info('-------------------------------------------------------')

    def _log_mechanize(self, host_response):
        logging.info('-------------------- HTTP response --------------------')
        logging.info(f'status code: {host_response.code}')
        logging.info(f'headers: {host_response.info()}')
        logging.info('-------------------------------------------------------')

    def _hardware_id():

        # tolino wants to know a few details about the HTTP client hardware
        # when it connects.
        #
        # 1233X-44XXX-XXXXX-XXXXX-XXXXh
        #
        # 1  = os id
        # 2  = browser engine id
        # 33 = browser id
        # 44 = browser version
        # X  = the result of a fingerprinting image

        os_id = {
            'Windows': '1',
            'Darwin': '2',
            'Linux': '3'
            }.get(platform.system(), 'x')

        # The hardware id contains some info about the browser
        #
        # Hey, tolino developers: Let me know which id values to use here
        engine_id = 'x'
        browser_id = 'xx'
        version_id = '00'

        # For some odd reason, the tolino javascript draws the text
        # "www.tolino.de" and a rectangle filled with the offical Telekom
        # magenta #E20074 (http://de.wikipedia.org/wiki/Magenta_%28Farbe%29)
        # into an image canvas and then fuddles around with the
        # base64-encoded PNG. Probably to gain some sort of fingerprint,
        # but it's not quite clear how this would help the tolino API.
        #
        # Hey, tolino developers: Let me know what you need here.

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

    def __init__(self, server_name='www.buecher.de'):

        if server_name not in servers_settings:
            raise PytolinoException(f'no partner {server_name} found')

        self.access_token = None
        self.refresh_token = None
        self.token_expires = None

        self.server_settings = servers_settings[server_name]
        self.session = requests.session()
        self.browser = mechanize.Browser()
        self.server_name = server_name

    def login(self, username, password):
        """login to the partner and get access token.

        :username: str
        :password: str
        :returns: None, but raises pytolino exceptions if fail
        """
        logging.info(f'login to {self.server_name}...')

        self.browser.open(self.server_settings['login_url'])
        self.browser.select_form(id=self.server_settings['form_id'])
        self.browser[self.server_settings['username_field']] = username
        self.browser[self.server_settings['password_field']] = password
        host_response = self.browser.submit()

        for cookie in self.browser.cookiejar:
            self.session.cookies.set(cookie.name, cookie.value)

        logging.info(self.server_settings['login_cookie'])
        self._log_mechanize(host_response)
        if not self.server_settings['login_cookie'] in self.session.cookies:
            raise PytolinoException(f'login to {self.server_name} failed.')

        auth_code = ""

        params = {
            'client_id': self.server_settings['client_id'],
            'response_type': 'code',
            'scope': self.server_settings['scope'],
            'redirect_uri': self.server_settings['reader_url']
        }
        if 'login_form_url' in self.server_settings:
            params['x_buchde.skin_id'] = self.server_settings[
                    'x_buchde.skin_id']
            params['x_buchde.mandant_id'] = self.server_settings[
                    'x_buchde.mandant_id']
        host_response = self.session.get(
                self.server_settings['auth_url'],
                params=params,
                verify=True,
                allow_redirects=False,
                )

        self._log_requests(host_response)

        try:
            params = parse_qs(urlparse(
                host_response.headers['Location']
                ).query)
            auth_code = params['code'][0]
        except ValueError:
            raise PytolinoException('oauth code request failed.')

        # Fetch OAUTH access token
        host_response = self.session.post(
                self.server_settings['token_url'],
                data={
                    'client_id': self.server_settings['client_id'],
                    'grant_type': 'authorization_code',
                    'code': auth_code,
                    'scope': self.server_settings['scope'],
                    'redirect_uri': self.server_settings['reader_url']
                    },
                verify=True,
                allow_redirects=False,
                )
        self._log_requests(host_response)
        try:
            j = host_response.json()
            self.access_token = j['access_token']
            self.refresh_token = j['refresh_token']
            self.token_expires = int(j['expires_in'])
        except requests.JSONDecodeError:
            raise PytolinoException('oauth access token request failed.')

    def logout(self):
        """logout from tolino partner host

        """
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
        self._log_requests(host_response)
        if host_response.status_code != 200:
            raise PytolinoException('file upload failed.')
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


if __name__ == '__main__':
    main()
