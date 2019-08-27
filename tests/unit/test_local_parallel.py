from track.persistence import make_local
from track.structure import Project, TrialGroup, Trial
from multiprocessing import Process

from tests.config import remove

trial_hash = None
trial_rev = None


def increment():
    backend = make_local('file://test_parallel.json')
    trial = backend.get_trial(Trial(_hash=trial_hash, revision=trial_rev))[0]

    # there is no lock here so the number could have changed already
    count = trial.metadata.get('count', 0)
    backend.log_trial_metadata(trial, count=count + 1)


def test_local_parallel(woker_count=20):
    """Here we check that _update_count is atomic and cannot run out of sync.
    `count` and the other can because it does not happen inside the lock (first fetch then increment
    """

    global trial_hash, trial_rev

    # -- Create the object that are going to be accessed in parallel
    remove('test_parallel.json')
    backend = make_local('file://test_parallel.json')

    project_def = Project(name='test')
    project = backend.new_project(project_def)

    group_def = TrialGroup(name='test_group', project_id=project.uid)
    group = backend.new_trial_group(group_def)

    trial = backend.new_trial(
        Trial(
            parameters={'batch': 256},
            project_id=project.uid,
            group_id=group.uid)
    )

    count = trial.metadata.get('count', 0)
    backend.log_trial_metadata(trial, count=count)

    trial_hash, trial_rev = trial.uid.split('_')
    # -- Setup done

    processes = [Process(target=increment) for _ in range(0, woker_count)]
    print('-- Start')
    [p.start() for p in processes]
    [p.join() for p in processes]

    trial = backend.get_trial(trial)[0]

    # remove('test_parallel.json')
    print(trial.metadata)
    assert trial.metadata.get('_update_count', 0) == woker_count + 1, 'Parallel write should wait for each other'


if __name__ == '__main__':
    test_local_parallel()



