from track.structure import Trial, TrialGroup, Project
from track.distributed.cockroachdb import CockRoachDB
from track.persistence.cockroach import Cockroach


def test_cockroach_die():
    db = CockRoachDB(location='/tmp/cockroach', addrs='localhost')
    db.start(wait=True)

    for k, v in db.properties.items():
        print(k, v)

    db.stop()


def test_cockroach_inserts():
    from track.distributed.cockroachdb import CockRoachDB

    db = CockRoachDB(location='/tmp/cockroach', addrs='localhost:8125')
    db.start(wait=True)

    for k, v in db.properties.items():
        print(k, v)

    try:
        proto = Cockroach('cockroach://localhost:8125')

        proto.new_project(Project(name='test'))
        p = proto.get_project(Project(name='test'))
        print(p)

        g = TrialGroup(name='test', project_id=p.uid)
        proto.new_trial_group(g)
        g = proto.get_trial_group(TrialGroup(_uid=g.uid))
        print(g)

        t = Trial(parameters={'a': 1}, project_id=p.uid)
        proto.new_trial(t)
        t = proto.get_trial(t)
        print(t)

        print('--')
    except Exception as e:
        raise e

    finally:
        db.stop()


if __name__ == '__main__':

    # test_cockroach()
    pass
