from tests.e2e.end_to_end import end_to_end_train
import time
import pytest
from tests.config import is_travis, remove


def e2e_socketed(client=1, security_layer=None):
    remove('socketed.json')

    from track.persistence.socketed import start_track_server
    from multiprocessing import Process

    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()

    # (protocol, hostname, port)
    db = Process(target=start_track_server, args=('file://socketed.json', 'localhost', port, security_layer))
    db.start()

    time.sleep(1)

    security = ''
    if security_layer is not None:
        security = f'?security_layer={security_layer}'

    try:
        uri = [f'socket://localhost:{port}' + security] * client

        clients = [Process(target=end_to_end_train, args=(arg,)) for arg in uri]

        [c.start() for c in clients]

        [c.join() for c in clients]

    except Exception as e:
        db.terminate()
        raise e

    finally:
        db.terminate()
    remove('socketed.json')


def test_e2e_socketed():
    e2e_socketed(1)


def test_e2e_socketed_aes():
    e2e_socketed(1, security_layer='AES')


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_e2e_socketed_clients():
    e2e_socketed(2)


if __name__ == '__main__':
    import sys
    sys.stdout = sys.stderr
    e2e_socketed(1, security_layer='AES')
