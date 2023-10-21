#!/usr/bin/env python3


import os
import configparser


class PytolinoException(Exception)

SERVERS_SETTINGS_FN = 'servers_settings.ini'
SERVERS_SETTINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), SERVERS_SETTINGS_FN)
servers_settings = configparser.ConfigParser()
servers_settings.read(SERVERS_SETTINGS_FILE_PATH)


class Client(object):

    """create a client to communicate with a tolino partner (login, etc..)"""

    def __init__(self, server_name='www.buecher.de'):
        try:
            server_settings = servers_settings[server_name]
        except KeyError:
            raise PytolinoException