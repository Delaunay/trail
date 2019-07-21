from track.structure import Trial, TrialGroup, Project, Status

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

        p1 = Project(name='test')
        proto.new_project(p1)
        p2 = proto.get_project(p1)
        print(p1)
        assert p1.name == p2.name

        g1 = TrialGroup(name='test', project_id=p1.uid)
        proto.new_trial_group(g1)
        g2 = proto.get_trial_group(TrialGroup(_uid=g1.uid))
        print(g1)
        assert g1.name == g2.name

        trial1 = Trial(parameters={'a': 1}, project_id=p1.uid, group_id=g1.uid)
        proto.new_trial(trial1)
        trial2 = proto.get_trial(Trial(_hash=trial1.hash))

        print(trial1)
        assert len(trial2) == 1
        assert trial1.parameters == trial2[0].parameters

        # fetch by project_id
        # trials = proto.fetch_trials({'status': Status.CreatedGroup, 'group_id': g1.uid})
        # print(trials)

        # fetch by group_id
        trials = proto.fetch_trials({'group_id': g1.uid})
        assert len(trials) == 1
        assert trials[0].uid == trial1.uid

        # fetch by status
        trials = proto.fetch_trials({'status': Status.CreatedGroup, 'group_id': g1.uid})

        assert len(trials) == 1
        assert trials[0].uid == trial1.uid

        # fetch by status
        trials = proto.fetch_trials({'status': {'$in': ['CreatedGroup']}, 'group_id': g1.uid})

        assert len(trials) == 1
        assert trials[0].uid == trial1.uid

        proto.log_trial_metrics(trial1, step=2, epoch_loss=1)
        proto.log_trial_metrics(trial1, step=3, epoch_loss=2)
        proto.log_trial_metrics(trial1, step=4, epoch_loss=3)

        proto.log_trial_metrics(trial1, loss=3)
        proto.log_trial_metrics(trial1, loss=2)
        proto.log_trial_metrics(trial1, loss=1)

        trials = proto.fetch_trials({'group_id': g1.uid})
        assert len(trials) == 1

        print(trials[0].metrics)

        assert trials[0].metrics == {
            'loss': [3, 2, 1],
            'epoch_loss': {
                2: 1,
                3: 2,
                4: 3
            }
        }

        proto.fetch_trials({
            ''
        })

    except Exception as e:
        raise e

    finally:
        db.stop()


if __name__ == '__main__':

    test_cockroach_inserts()
    pass
