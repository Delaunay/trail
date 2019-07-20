from track.client import TrackClient, TrialDoesNotExist
from tests.config import Remove
import os


def test_client_no_group(file='client'):
    with Remove(file):
        client = TrackClient(f'file://{file}.json')
        client.set_project(name='test_client')

        log = client.new_trial()
        client.log_arguments(batch_size=256)

        client.log_metrics(step=1, epoch_loss=1)
        client.log_metrics(accuracy=0.98)

        client.save()
        client.report()

        print(log.trial.metrics)


def test_client_set_trial_throw(file='client_throw'):
    try:
        with Remove(file):
            client = TrackClient(f'file://{file}.json')
            client.set_trial(uid='does_not_exist')
    except TrialDoesNotExist:
        pass


# def test_client_no_group():
#     with Remove('client_test.json'):
#         client = TrackClient('file://client_test.json')
#         client.set_project(name='test_client')
#
#         trial = client.new_trial()
#         trial.log_arguments(batch_size=256)
#
#         trial.log_metrics(step=1, epoch_loss=1)
#         trial.log_metrics(accuracy=0.98)
#
#         client.save()
#         client.report()
#


def test_client_capture_output(file='client_output'):
    with Remove(file):
        client = TrackClient(f'file://{file}.json')
        client.set_project(name='project_name')
        client.new_trial()

        client.capture_output(50)

        for i in range(0, 100):
            print(f'testing_output_{i}')

        out = client.stdout.raw()
        for i in range(0, 25):
            assert out[i * 2] == f'testing_output_{100 - 25 + i}'
            assert out[i * 2 + 1] == '\n'


def test_client_orion_integration(file='client_orion'):
    def scoped_init():
        clt = TrackClient(f'file://{file}.json')

        clt.set_project(name='project_name')
        clt.set_group(name='group_name')
        clt.new_trial()
        clt.log_arguments(batch_size=256)

        clt.save()
        return clt.trial.uid

    old_environ = os.environ.copy()
    try:
        with Remove(file):
            trial_id = scoped_init()

            os.environ['ORION_PROJECT'] = 'project_name'
            os.environ['ORION_EXPERIMENT'] = 'group_name'
            os.environ['ORION_TRIAL_ID'] = trial_id

            client = TrackClient(f'file://{file}.json')

            assert client.trial.parameters['batch_size'] == 256

    finally:
        os.environ = old_environ


if __name__ == '__main__':
    test_client_capture_output()
    test_client_no_group()
    test_client_set_trial_throw()
    test_client_orion_integration()

