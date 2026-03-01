import unittest
from pathlib import Path
import tomllib


from pytolino import server_settings_keys
from pytolino.tolino_cloud import servers_settings


class TestKeys(unittest.TestCase):

    """test for keys for server settings toml"""
    def test_keys(self):
        for server_settings in servers_settings.values():
            for key in dir(server_settings_keys):
                key: str
                if not key.startswith("__"):
                    self.assertIn(key, server_settings)
