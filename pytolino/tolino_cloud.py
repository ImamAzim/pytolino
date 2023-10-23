#!/usr/bin/env python3


import os
import configparser
import platform


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

        self.server_settings = servers_settings[server_name]
        self.session = requests.session()
        self.browser = mechanize.Browser()


if __name__ == '__main__':
    main()
