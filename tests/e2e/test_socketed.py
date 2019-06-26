from tests.e2e.end_to_end import end_to_end_train
import time


def e2e_socketed(client=1):
    from track.persistence.socketed import start_track_server
    from multiprocessing import Process

    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()

    # (protocol, hostname, port)
    db = Process(target=start_track_server, args=('file://socketed.json', 'localhost', port))
    db.start()

    time.sleep(1)

    try:
        uri = [f'socket://localhost:{port}'] * client

        clients = [Process(target=end_to_end_train, args=(arg,)) for arg in uri]

        [c.start() for c in clients]

        [c.join() for c in clients]

    except Exception as e:
        db.terminate()
        raise e

    finally:
        db.terminate()


def test_e2e_socketed():
    e2e_socketed(1)


def test_e2e_socketed_clients():
    e2e_socketed(2)


if __name__ == '__main__':
    test_e2e_socketed_clients()

