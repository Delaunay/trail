********
Backends
********

Track was made to support different backends, you can even implement your own!


Local Backend
-------------

Track implements a local storage backend for quick and simple experiments

.. code-block:: python

    client = TrackClient(f'file://report.json')


CockroachDB backend
-------------------

Track implements a backend that can use a running cockroachdb instance as storage.

.. code-block:: python

    address = '127.0.0.1
    port = 8123
    client = TrackClient(f'cockroach://{address}:{port}')



Socket backend
--------------

Track implements a backend that uses sockets to forward request to a remote server

Server
^^^^^^

Simple servers that receive request from the client and forwards all request to another backend.
The example below forwards all request to the local backend, allowing to have a single process modifying the file.

.. code-block:: python

    from track.persistence.socketed import start_track_server

    address = '127.0.0.1
    port = 8123
    layer = 'AES'
    start_track_server('file:server_test.json', address, port, backend=layer)



Client
^^^^^^

Start a client that forwards all request to a remote server

.. code-block:: python

    username = ...
    password = ...
    address = '127.0.0.1
    port = 8123
    layer = 'AES'            # supported AES or (None, i.e put nothing)
    client = TrackClient(f'socket://{username}:{password}@{address}:{port}?security_layer={layer}')


Bring Your Own Backend
----------------------

To implement you own you can simply extend :class:`track.persistence.protocol.Protocol`


.. code-block:: python

    from track.persistence import register
    from track.persistence.protocol import Protocol

    class MyOwnBackend(Protocol):
        ....


    register('byob', MyOwnBackend)

You can then use it naturally


.. code-block:: python

    client = TrackClient('byob://....)

