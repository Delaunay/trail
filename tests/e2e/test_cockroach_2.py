from tests.e2e.end_to_end import end_to_end_train
from multiprocessing import Process
from tests.config import is_travis
import pytest


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_e2e_cockroach_2clients(count=2):
    from track.distributed.cockroachdb import CockRoachDB

    db = CockRoachDB(location='/tmp/cockroach', addrs='localhost:8124')
    db.start(wait=True)

    try:
        uri = 'cockroach://localhost:8124'

        clients = [Process(target=end_to_end_train, args=(uri,)) for _ in range(count)]

        [c.start() for c in clients]

        [c.join() for c in clients]

    except Exception as e:
        raise e

    finally:
        db.stop()


if __name__ == '__main__':

    test_e2e_cockroach_2clients(count=4)
