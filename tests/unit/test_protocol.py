import os

from track.persistence import get_protocol
from track.structure import Trial, TrialGroup, Project, Status, CustomStatus

new = CustomStatus('new', Status.CreatedGroup.value + 1)
reserved = CustomStatus('reserved', Status.CreatedGroup.value + 2)


project = Project(
    name='test'
)

group = TrialGroup(
    name='MyGroup',
    project_id=project.uid
)


statuses = [
    Status.Interrupted,
    Status.Broken,
    Status.Completed,
    reserved,
    new, new, new, new, new
]
trials = []
for idx, status in enumerate(statuses):
    trial = Trial(
        project_id=project.uid,
        group_id=group.uid,
        status=Status.Interrupted,
        parameters={
            'batch_size': 256,
            'id': idx
        }
    )
    trials.append(trial)

TRIAL_COUNT = len(trials)


def remove(filename):
    try:
        os.remove(filename)
    except:
        pass


def make_storage(backend, delete=True):
    if delete:
        remove('test.json')

    proto = get_protocol(backend)

    if delete:
        proto.new_project(project)
        proto.new_trial_group(group)
        for t in trials:
            assert proto.new_trial(t) is not None

    return proto


def test_inserted_trial(backend='file://test.json'):
    proto = make_storage(backend)
    assert len(proto.fetch_trials({})) == TRIAL_COUNT
    print('Trial', proto.fetch_trials({})[0])


def test_inserted_group(backend='file://test.json'):
    proto = make_storage(backend)
    assert len(proto.fetch_groups({})) == 1
    print('Group', proto.fetch_groups({})[0])


def test_inserted_project(backend='file://test.json'):
    proto = make_storage(backend)
    assert len(proto.fetch_projects({})) == 1
    print('Project', proto.fetch_projects({})[0])


def test_fetch_trials(backend='file://test.json'):
    proto = make_storage(backend)
    query = dict(group_id=group.uid)
    trials = proto.fetch_trials(query)
    assert len(trials) == TRIAL_COUNT


def test_fetch_and_update_trial(backend='file://test.json'):
    proto = make_storage(backend)
    query = dict(group_id=group.uid)
    t = proto.fetch_and_update_trial(
        query,
        'set_trial_status',
        status=reserved)

    assert t is not None
    t = proto.fetch_trials({'uid': t.uid})[0]
    assert t.status == reserved


def test_update_trial_by_status(backend='file://test.json'):
    proto = make_storage(backend)

    query = dict(
        status={'$in': ['new', 'suspended', 'interrupted']}
    )

    t = proto.fetch_and_update_trial(
        query,
        'set_trial_status',
        status=reserved)

    assert t is not None
    t = proto.fetch_trials({'uid': t.uid})[0]
    assert t.status == reserved


def test_update_trial_by_status_and_group(backend='file://test.json', delete=True, queue=None):
    from track.utils import ItemNotFound
    proto = make_storage(backend, delete=delete)

    query = dict(
        group_id=group.uid,
        status={'$in': ['new', 'suspended', 'interrupted']}
    )

    try:
        t = proto.fetch_and_update_trial(
            query,
            'set_trial_status',
            status=reserved)
    except ItemNotFound:
        t = None

    if delete:
        assert t is not None
        t = proto.fetch_trials({'uid': t.uid})[0]
        assert t.status == reserved

    if queue is not None and t is not None:
        queue.put(t.uid)

    return t


def test_update_group(backend='file://test.json'):
    proto = make_storage(backend)

    result_group = proto.fetch_groups({
        '_uid': group.uid
    })

    assert len(result_group) == 1


def test_fetch_and_update_group(backend='file://test.json'):
    proto = make_storage(backend)

    result_group = proto.fetch_and_update_group({
            '_uid': group.uid
        }, 'set_group_metadata', field_info_new=True)

    assert result_group.metadata.get('field_info_new') is not None

    fetched_group = proto.fetch_groups({
        '_uid': group.uid
    })[0]

    assert fetched_group.metadata.get('field_info_new') is not None


def retrieve_trials(queue):
    reserved_trial = []
    running = True

    while running:
        try:
            r = queue.get(timeout=1)
            if r is not None:
                reserved_trial.append(r)
            else:
                running = False
        except:
            running = False

    return reserved_trial


def reserve_trials(workers, backend, queue):
    from multiprocessing import Process
    ws = []

    # Reserve a few trials
    for i in range(workers):
        p = Process(target=test_update_trial_by_status_and_group, args=(backend, False, queue))
        ws.append(p)

    # Run all the workers at once
    for w in ws:
        w.start()

    for w in ws:
        w.join()


def get_reservable_trials(backend):
    proto = make_storage(backend)

    query = dict(
        group_id=group.uid,
        status={'$in': ['new', 'suspended', 'interrupted']}
    )

    trials = proto.fetch_trials(query)
    reservable = []

    for t in trials:
        reservable.append(t.uid)

    return proto, set(reservable)


def test_parallel_fetch_update(backend='file://test.json', workers=12):
    from multiprocessing import Queue

    proto, reservable = get_reservable_trials(backend)

    queue = Queue()

    reserve_trials(workers, backend, queue)

    reserved_trial = retrieve_trials(queue)
    assert len(reserved_trial) == len(set(reserved_trial)), 'All reserved trials should be different'

    reserved_trial = set(reserved_trial)
    intersect = reservable.intersection(reserved_trial)
    assert len(reserved_trial) == len(intersect), 'All reserved trials should be reservable'

    for uid in reserved_trial:
        t = Trial()
        t.uid = uid

        trial = proto.get_trial(t)[0]
        assert trial.status.name == 'reserved'


if __name__ == '__main__':
    import sys
    sys.stderr = sys.stdout

    # test_update_group()
    # test_fetch_and_update_trial()
    test_parallel_fetch_update()
    # test_update_trial_by_status()
    # test_update_trial_by_status_and_group()

    # test_inserted_project()
    # test_inserted_group()
    # test_inserted_trial()
    #
    # test_fetch_trials()
    # test_fetch_and_update_trial()

    # test_update_group()
    # test_update_trial()



