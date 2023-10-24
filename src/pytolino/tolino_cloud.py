#!/usr/bin/env python3


import os
import configparser
import platform
import logging


import requests
import mechanize


class PytolinoException(Exception):
    pass


SERVERS_SETTINGS_FN = 'servers_settings.ini'
SERVERS_SETTINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), SERVERS_SETTINGS_FN)
servers_settings = configparser.ConfigParser()
servers_settings.read(SERVERS_SETTINGS_FILE_PATH)


def main():
    print(SERVERS_SETTINGS_FILE_PATH)
    print(servers_settings.sections())


class Client(object):

    """create a client to communicate with a tolino partner (login, etc..)"""

    def _log_host_response(self, host_response):
        logging.info('-------------------- HTTP response --------------------')
        logging.info('status code: {}'.format(host_response.status_code))
        logging.info('cookies: {}'.format(pformat(host_response.cookies)))
        logging.info('headers: {}'.format(pformat(host_response.headers)))
        try:
            j = host_response.json()
            logging.debug('json: {}'.format(pformat(j)))
        except:
            logging.debug('text: {}'.format(host_response.text))
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
            'Windows' : '1',
            'Darwin'  : '2',
            'Linux'   : '3'
            }.get(platform.system(), 'x')

        # The hardware id contains some info about the browser
        #
        # Hey, tolino developers: Let me know which id values to use here
        engine_id  = 'x'
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

        return (os_id +
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
            'h')

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
        """login to the partner and get access token

        :username: str
        :password: str
        :returns: None, but raises pytolino exceptions if fail. will print ansers
        """
        logging.info(f'login to {self.server_name}...')

        self.browser.open(self.server_settings['login_url'])
        self.browser.select_form(id=self.server_settings['form_id'])
        self.browser[self.server_settings['username_field'] = username
        self.browser[self.server_settings['password_field'] = password
        host_response = self.browser.submit()

        for cookie in self.browser.cookiejar:
            self.session.cookies.set(cookie.name, cookie.value)

        logging.info(self.server_settings['login_cookie'])
        self._log_host_response(host_response)
        if not self.server_settings['login_cookie'] in s.cookies:
            raise PytolinoException(f'login to {self.server_name} failed.')

        # auth_code = ""
        # if 'tat_url' in c:
            # try:
                # r = s.get(c['tat_url'], verify=True)
                # self._debug(r)
                # b64 = re.search(r'\&tat=(.*?)%3D', r.text).group(1)
                # self.access_token = base64.b64decode(b64+'==').decode('utf-8')
            # except:
                # raise TolinoException('oauth access token request failed.')
        # else:
            # # Request OAUTH code
            # params = {
                # 'client_id'     : c['client_id'],
                # 'response_type' : 'code',
                # 'scope'         : c['scope'],
                # 'redirect_uri'  : c['reader_url']
            # }
            # if 'login_form_url' in c:
                # params['x_buchde.skin_id'] = c['x_buchde.skin_id']
                # params['x_buchde.mandant_id'] = c['x_buchde.mandant_id']
            # r = s.get(c['auth_url'], params=params, verify=True, allow_redirects=False)
            # self._debug(r)
            # try:
                # params = parse_qs(urlparse(r.headers['Location']).query)
                # auth_code = params['code'][0]
            # except:
                # raise TolinoException('oauth code request failed.')

            # # Fetch OAUTH access token
            # r = s.post(c['token_url'], data = {
                # 'client_id'    : c['client_id'],
                # 'grant_type'   : 'authorization_code',
                # 'code'         : auth_code,
                # 'scope'        : c['scope'],
                # 'redirect_uri' : c['reader_url']
            # }, verify=True, allow_redirects=False)
            # self._debug(r)
            # try:
                # j = r.json()
                # self.access_token = j['access_token']
                # self.refresh_token = j['refresh_token']
                # self.token_expires = int(j['expires_in'])
            # except:
                # raise TolinoException('oauth access token request failed.')

if __name__ == '__main__':
    main()
