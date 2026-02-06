UPDATE
===========

because of heavy anti-bot protection, it is no longer possible to make a fully automatic login. One can however reuse authorization token after a manual login. The token can then be refreshed automatically, for example with a cronjob (at least once per hour.)


pytolino
===================

A client to interact (login, upload, delete ebooks, etc..) with the tolino cloud with python. thanks to https://github.com/darkphoenix/tolino-calibre-sync for the inspiration.

One difference is that I aim to create a python package from it and to put it on pypi, so that one can use this python module in other projects.

Installation
============

.. code-block:: bash

    pip install pytolino

Usage
=====

First, login manually, and use an inspector tool in the browser to inspect the requests. After connecting to the digital libray of tolino, there is POST request (named token). From the request response, copy the value of the refresh token (and the expiration time in seconds). Then, in a PATH request, in the request header, find the device_id number.

You can then store the token:

.. code-block:: python

    from pytolino.tolino_cloud import Client
    partner = 'orellfuessli'
    account_name = 'any name for reference'
    client = Client(partner)
    print('login on your browser and get the token.')
    refresh_token = input('refresh token:\n')
    expires_in = int(input('expires_in:\n'))
    hardware_id = input('hardware id:\n')
    Client.store_token(
    account_name, refresh_token, expires_in, hardware_id)

Then, get a new access token. It will expires in 1 hours, so you might want to create a crontab job to do it regularely:

.. code-block:: python

    from pytolino.tolino_cloud import Client
    partner = 'orellfuessli'
    account_name = 'any name for reference'
    client = Client(partner)
    client.get_new_token(account_name)

After this, instead of login, you only need to retrieve the access token that is stored on disk and upload, delete books, etc...

.. code-block:: python

    from pytolino.tolino_cloud import Client
    partner = 'orellfuessli'
    account_name = 'any name for reference'
    client = Client(partner)
    client.retrieve_token(account_name)

    ebook_id = client.upload(EPUB_FILE_PATH) # return a unique id that can be used for reference
    client.add_collection(epub_id, 'science fiction') # add the previous book to the collection science-fiction
    client.add_cover(epub_id, cover_path) # to upload a cover on the book.
    client.delete_ebook(epub_id) # delete the previousely uploaded ebook
    inventory = client.get_inventory() # get a list of all the books on the cloud and their metadata
    client.upload_metadata(epub_id, title='my title', author='someone') # you can upload various kind of metadata


To get a list of the supported partners:

.. code-block:: python

   from pytolino.tolino_cloud import PARTNERS
   print(PARTNERS)

for now, only orelfuessli is supported, but it should be easy to include the others (but always need of a manual login)


Features
========

* upload ebook
* delete ebook from the cloud
* add a book to a collection
* download inventory
* upload metadata


License
=======

The project is licensed under GNU GENERAL PUBLIC LICENSE v3.0
