from pathlib import Path


import xdg_base_dirs


APP_NAME = 'pytolino'

cache_folder = xdg_base_dirs.xdg_cache_home() / APP_NAME
cache_folder.mkdir(parents=True, exist_ok=True)

