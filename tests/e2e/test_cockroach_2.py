from tests.e2e.end_to_end import end_to_end_train
from multiprocessing import Process


def test_e2e_cockroach_2clients():
    from track.distributed.cockroachdb import CockRoachDB

    db = CockRoachDB(location='/tmp/cockroach', addrs='localhost:8123')
    db.start(wait=True)

    try:
        uri = 'cockroach://localhost:8123'

        c1 = Process(target=end_to_end_train, args=(uri,))
        c2 = Process(target=end_to_end_train, args=(uri,))

        c1.start()
        c2.start()

        c1.join()
        c2.join()

    except Exception as e:
        raise e

    finally:
        db.stop()


if __name__ == '__main__':

    test_e2e_cockroach_2clients()
