import os

from track.persistence import get_protocol
from track.structure import Trial, TrialGroup, Project, Status, CustomStatus


reserved = CustomStatus('reserved', Status.CreatedGroup.value + 2)


project = Project(
    name='test'
)

group = TrialGroup(
    name='MyGroup',
    project_id=project.uid
)

trials = []
for idx, status in enumerate([Status.Interrupted, Status.Broken, Status.Completed, reserved]):
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


def make_storage(backend):
    remove('test.txt')
    proto = get_protocol(backend)
    proto.new_project(project)
    proto.new_trial_group(group)
    for t in trials:
        assert proto.new_trial(t) is not None

    return proto


def test_inserted_trial(backend='file://test.txt'):
    proto = make_storage(backend)
    assert len(proto.fetch_trials({})) == TRIAL_COUNT
    print('Trial', proto.fetch_trials({})[0])


def test_inserted_group(backend='file://test.txt'):
    proto = make_storage(backend)
    assert len(proto.fetch_groups({})) == 1
    print('Group', proto.fetch_groups({})[0])


def test_inserted_project(backend='file://test.txt'):
    proto = make_storage(backend)
    assert len(proto.fetch_projects({})) == 1
    print('Project', proto.fetch_projects({})[0])


def test_fetch_trials(backend='file://test.txt'):
    proto = make_storage(backend)
    query = dict(group_id=group.uid)
    trials = proto.fetch_trials(query)
    assert len(trials) == TRIAL_COUNT


def test_fetch_and_update_trial(backend='file://test.txt'):
    proto = make_storage(backend)
    query = dict(group_id=group.uid)
    t = proto.fetch_and_update_trial(
        query,
        'set_trial_status',
        status=reserved)

    assert t is not None
    t = proto.fetch_trials({'uid': t.uid})[0]
    assert t.status == reserved


def test_update_trial_by_status(backend='file://test.txt'):
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


def test_update_trial_by_status_and_group(backend='file://test.txt'):
    proto = make_storage(backend)

    query = dict(
        group_id=group.uid,
        status={'$in': ['new', 'suspended', 'interrupted']}
    )

    t = proto.fetch_and_update_trial(
        query,
        'set_trial_status',
        status=reserved)

    assert t is not None
    t = proto.fetch_trials({'uid': t.uid})[0]
    assert t.status == reserved


def test_update_group(backend='file://test.txt'):
    proto = make_storage(backend)

    result_group = proto.fetch_groups({
        '_uid': group.uid
    })

    assert len(result_group) == 1


def test_fetch_and_update_group(backend='file://test.txt'):
    proto = make_storage(backend)

    result_group = proto.fetch_and_update_group({
            '_uid': group.uid
        }, 'set_group_metadata', field_info_new=True)

    print('Updating 3: ', id(result_group))
    assert result_group.metadata.get('field_info_new') is not None

    fetched_group = proto.fetch_groups({
        '_uid': group.uid
    })[0]

    print('Updating 4: ', id(fetched_group))

    assert fetched_group.metadata.get('field_info_new') is not None


if __name__ == '__main__':
    # test_update_group()
    # test_fetch_and_update_trial()
    test_fetch_and_update_group()
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



