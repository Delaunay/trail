from tests.config import is_travis,  multi_client_launch
import pytest

try:
    from pytest_cov.embed import cleanup_on_sigterm
except ImportError:
    pass
else:
    cleanup_on_sigterm()


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_e2e_cockroach_2clients(count=2):
    from track.distributed.cockroachdb import CockRoachDB

    db = CockRoachDB(location='/tmp/cockroach', addrs='localhost:8124')
    db.start(wait=True)

    try:
        multi_client_launch('cockroach://localhost:8124', count)
    except Exception as e:
        raise e

    finally:
        db.stop()


if __name__ == '__main__':

    test_e2e_cockroach_2clients(count=2)
