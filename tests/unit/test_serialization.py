from track.struct import Status, Project, TrialGroup,Trial
from track.serialization import to_json, from_json


def test_project():
    p = Project(
        uid='0',
        name='1',
        description='2',
        tags=['0', '1'],
        groups=[TrialGroup()],
        trials=[]
    )

    ps = from_json(to_json(p))
    assert p == ps


def test_trial_group():
    p = TrialGroup(
        uid='0',
        name='1',
        description='2',
        tags=['0', '1'],
        trials=[]
    )

    ps = from_json(to_json(p))
    assert p == ps


def test_trial():
    p = Trial(
        uid='0',
        name='1',
        description='2',
        tags=['0', '1'],
        version='01',
        group_id='0',
        project_id='1',
        parameters=dict(a=1, b=2),
        metadata=dict(a=2, b=3),
        metrics=dict(a=3, b=4),
        chronos=dict(a=4, b=5),
        status=Status.FinishedGroup,
        errors=[]
    )

    ps = from_json(to_json(p))

    # status is not serializable perfectly because we allow for custom status
    ps.status = p.status
    assert p == ps


if __name__ == '__main__':
    test_project()
    test_trial_group()
    test_trial()
