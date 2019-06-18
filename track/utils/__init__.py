import ssl
import socket


def open_socket(add, port, backend=None):

    if backend is None:
        return socket.create_connection((add, port))

    if backend == 'ssl':
        context = ssl.create_default_context()
        sckt = socket.create_connection((add, port))
        return context.wrap_socket(sckt, server_hostname=add, server_side=False)

    from track.utils.encrypted import EncryptedSocket
    return EncryptedSocket().open(add, port)


def listen_socket(add, port, backend=None):
    if backend is None:
        sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sckt.bind((add, port))
        sckt.listen()
        return sckt

    if backend == 'ssl':
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # context.load_cert_chain(f'{temp_dir}/server.crt', f'{temp_dir}/server.key')

        sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sckt.bind((add, port))
        sckt.listen()
        return context.wrap_socket(sckt, server_side=True)

    from track.utils.encrypted import EncryptedSocket
    return EncryptedSocket().listen(add, port)


if __name__ == '__main__':
    print(ssl.HAS_SNI)
