from track.client import TrackClient
import pdb


def test_trial():

    client = TrackClient('file:test.json')

    client.set_project(name='ConvnetTest', description='Trail test example')
    client.set_group(name='test_group')

    logger = client.new_trial()
    client.get_arguments({'a': 1})

    uid1 = logger.trial.hash

    logger = client.new_trial()
    client.get_arguments({'a': 2})

    uid2 = logger.trial.hash

    assert uid1 != uid2, 'Trials with different parameters must have different hash'


if __name__ == '__main__':
    test_trial()
