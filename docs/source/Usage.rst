Usage
=====


Before being able to send requests, you need to register your computer on which you will run the code:

.. code-block:: python

    from pytolino.tolino_cloud import Client, PytolinoException
    client = Client()
    client.login(USERNAME, PASSWORD)
    client.register() # do this only once!
    client.logout()

You can then upload or delete ebook on your cloud:

.. code-block:: python

    from pytolino.tolino_cloud import Client, PytolinoException
    client = Client()
    client.login(USERNAME, PASSWORD)
    ebook_id = client.upload(EPUB_FILE_PATH) # return a unique id that can be used for reference
    client.delete_ebook(epub_id) # delete the previousely uploaded ebook
    client.logout()


if you want to unregister your computer:

.. code-block:: python

    from pytolino.tolino_cloud import Client, PytolinoException
    client = Client()
    client.login(USERNAME, PASSWORD)
    client.register() # now you will not be able to upload books from this computer
    client.logout()
