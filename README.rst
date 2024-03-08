pytolino
===================

A client to interact (login, upload, delete ebooks, etc..) with the tolino cloud with python. Most of the code is forked from https://github.com/darkphoenix/tolino-calibre-sync

One difference is that I aim to create a python package from it and to put it on pypi, so that one can use this python module in other projects.

Installation
============

.. code-block:: bash

    pip install pytolino

Usage
=====


Before being able to send requests, you need to register your computer on which you will run the code:

.. code-block:: python

    from pytolino.tolino_cloud import Client, PytolinoException
    client = Client()
    client.login(USERNAME, PASSWORD)
    client.register() # do this only once!
    client.logout()

You can then upload, add to a collection or delete ebook on your cloud:

.. code-block:: python

    from pytolino.tolino_cloud import Client, PytolinoException
    client = Client()
    client.login(USERNAME, PASSWORD)
    ebook_id = client.upload(EPUB_FILE_PATH) # return a unique id that can be used for reference
    client.add_collection(epub_id, 'science fiction') # add the previous book to the collection science-fiction
    client.add_cover(epub_id, cover_path) # to upload a cover on the book.
    client.delete_ebook(epub_id) # delete the previousely uploaded ebook
    inventory = client.get_inventory() # get a list of all the books on the cloud and their metadata
    client.upload_metadata(epub_id, title='my title', author='someone') # you can upload various kind of metadata
    client.logout()


if you want to unregister your computer:

.. code-block:: python

    from pytolino.tolino_cloud import Client, PytolinoException
    client = Client()
    client.login(USERNAME, PASSWORD)
    client.register() # now you will not be able to upload books from this computer
    client.logout()

By default, it will connect to 'www.buecher.de'. In principle you could change the partner with:

.. code-block:: python

   client = Client(server_name='www.orelfuessli') # for example if you have an account at orel fuessli.

To get a list of the supported partners:

.. code-block:: python

   from pytolino.tolino_cloud import PARTNERS
   print(PARTNERS)

Unfortunately, the only supported partner now is 'www.buecher.de', because it has a different way of connection... So for now, the only solution is to create an account there and link it to your original account.



Features
========

* login to tolino partner (for now works only with buecher.de)
* register device
* unregister device
* upload ebook
* delete ebook from the cloud
* add a book to a collection
* download inventory
* upload metadata
* more to come...


License
=======

The project is licensed under GNU GENERAL PUBLIC LICENSE v3.0
