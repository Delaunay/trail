from track.client import TrackClient
import pdb


def test_trial():

    client = TrackClient('file:test.json')

    client.set_project(name='ConvnetTest', description='Trail test example')
    client.set_group(name='test_group')

    trial = client.new_trial()
    client.get_arguments({'a': 1})

    uid1 = trial.trial.hash

    trial = client.new_trial()
    client.get_arguments({'a': 2})

    uid2 = trial.trial.hash

    print(uid1, uid2)


if __name__ == '__main__':

    pdb.set_trace()
    test_trial()
