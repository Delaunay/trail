from tests.e2e.end_to_end import end_to_end_train
import time


def test_e2e_socketed():
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
        end_to_end_train(f'socket://localhost:{port}')

    except Exception as e:
        db.terminate()
        raise e

    finally:
        db.terminate()


if __name__ == '__main__':

    test_e2e_socketed()

