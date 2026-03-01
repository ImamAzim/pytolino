import unittest
from pathlib import Path
import tomllib


from pytolino import server_settings_keys
from pytolino.tolino_cloud import servers_settings


class TestKeys(unittest.TestCase):

    """test for keys for server settings toml"""
    def test_keys(self):
        for server_settings in servers_settings.values():
            for key_var in dir(server_settings_keys):
                key_var: str
                if not key_var.startswith("__"):
                    key = getattr(server_settings_keys, key_var)
                    self.assertIn(key, server_settings)
