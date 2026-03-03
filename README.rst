UPDATE
===========

because of heavy anti-bot protection, it is no longer possible to make a fully automatic login on a headless device. If one is not on a headless device, it will login using seleniubbase, but you might have to install chromium browser. On a headless device, one can import manually a refresh token. It can be used to get a new access token, (for example regulary witha cronjob), but it will eventually expire after 10 hours.


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
First, one need to login.
if chromium browser is installed and there is a monitor, it can be done automaticaly:

.. code-block:: python
    from pytolino.tolino_cloud import Client
    partner = 'orellfuessli'
    client = Client(partner=partner,username='USERNAME)
    client.login('PASSWORD')
if this is the first login on the device, it will use selenium and store an access token on the device.

On a headless device, one can instead import a refresh token:
First, login manually with another device, and use an inspector tool in the browser to inspect the requests. After connecting to the digital libray of tolino, there is POST request (named token). From the request response, copy the value of the refresh token. Then, in a PATCH request, in the request header, find the device_id number.

You can then import the token:

.. code-block:: python
    client = Client(username='USERNAME')
    print('please login manually and use inspector tool to find refresh token'
          ' in a token request')
    refresh_token = input('refresh login: ')
    print('find the hardware id in the request header '
          'of a patch request for example')
    hardware_id = input('hardware id: ')
    client.import_token(refresh_token, hardware_id)
    client.login('PASSWORD', allow_GUI_autologin=False)  # seleniumbase will not be used


After this, the login will method will only refresh the access token for on hour, and you can work with the libraty:

.. code-block:: python
    try:
        client.login(password)
    except PytolinoException as e:
        print(e)
    else:
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
