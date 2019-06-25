from tests.e2e.end_to_end import end_to_end_train


def test_e2e_cockroach():
    from track.distributed.cockroachdb import CockRoachDB

    db = CockRoachDB(location='/tmp/cockroach', addrs='localhost:8123')
    db.start(wait=True)

    try:
        end_to_end_train('cockroach://localhost:8123')
    except Exception as e:
        raise e

    finally:
        db.stop()

