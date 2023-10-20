tolino cloud client
============

work in progress..

a client to interact (login, upload, delete ebooks, etc..) with the tolino cloud with python. Most of the code is forked from https://github.com/darkphoenix/tolino-calibre-sync

one difference is that I aim to create a python package from it and to put it on pypi, so that one can use this python module in other projects.

example:
from tolino_client import TolinoCloud
tolino = TolinoCloud()
tolino.login(username, password)
tolino.register_device()
tolino.upload('/path_to_my_epub_gile')
tolino.logout()

Features
--------

connect to tolino cloud (work only with buecher.de partner)
login, register, upload epubs, delete, list, download...


Installation
------------

pip install tolino_cloud_client

License
-------

The project is licensed under GNU GENERAL PUBLIC LICENSE v3.0
