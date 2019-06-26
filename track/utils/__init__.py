import socket


def open_socket(add, port, backend=None):
    sckt = socket.create_connection((add, port))

    if backend is None:
        return sckt

    if backend == 'ssl':
        import ssl

        context = ssl.create_default_context()
        return context.wrap_socket(sckt, server_hostname=add, server_side=False)

    elif backend == 'AES':
        from track.utils.encrypted import wrap_socket

        return wrap_socket(sock=sckt, server_side=False)


def listen_socket(add, port, backend=None):
    sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sckt.bind((add, port))
    sckt.listen()

    if backend is None:
        return sckt

    if backend == 'ssl':
        import ssl

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        return context.wrap_socket(sckt, server_side=True)

    elif backend == 'AES':
        from track.utils.encrypted import wrap_socket

        return wrap_socket(sock=sckt, server_side=True)
