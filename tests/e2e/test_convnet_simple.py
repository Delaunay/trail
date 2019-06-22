import sys

from tests.e2e.end_to_end import end_to_end_train
from track.persistence.socketed import start_track_server
from multiprocessing import Process

sys.stderr = sys.stdout


SKIP_COMET = True
SKIP_SERVER = True


def test_e2e_file():
    end_to_end_train('file://file_test.json')


def test_e2e_server_socket():
    if SKIP_SERVER:
        return

    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()

    print('Starting Server')
    #start_track_server('file://server_test.json', 'localhost', port)

    server = Process(target=start_track_server('file://server_test.json', 'localhost', port))
    server.start()

    print('Starting client')

    end_to_end_train(f'socket://test:123@localhost:{port}')


def test_e2e_cometml():
    if SKIP_COMET:
        return

    end_to_end_train('cometml:/convnet-test/convnet')
