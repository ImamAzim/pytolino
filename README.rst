tolino cloud client
===================

a client to interact (login, upload, delete ebooks, etc..) with the tolino cloud with python. Most of the code is forked from https://github.com/darkphoenix/tolino-calibre-sync

one difference is that I aim to create a python package from it and to put it on pypi, so that one can use this python module in other projects.

Installation
============

pip install tolino_cloud_client

Usage
=====

.. code-block:: python
   :caption: before being able to send requests, you need to register your computer on which you will run the code.

        from pytolino.tolino_cloud import Client, PytolinoException


        client = Client()
        client.login(USERNAME, PASSWORD)
        client.register() # do this only once!
        client.logout()

..example:
..from tolino_client import TolinoCloud
..tolino = TolinoCloud()
..tolino.login(username, password)
..tolino.register_device()
..tolino.upload('/path_to_my_epub_gile')
..tolino.logout()

Features
========

* login to tolino partner (for now works only with buecher.de)
* register device
* unregister device
* upload ebook
* delete ebook from the cloud
* more to come...


License
=======

The project is licensed under GNU GENERAL PUBLIC LICENSE v3.0
