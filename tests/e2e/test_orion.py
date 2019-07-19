import orion.core.cli
from tests.config import is_travis, remove
from multiprocessing import Process
import pytest
import subprocess
import os
import shutil
import time


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_orion_poc(backend='track:file://orion_results.json?objective=epoch_loss'):
    remove('orion_results.json')

    os.environ['ORION_STORAGE'] = backend
    _, uri = os.environ.get('ORION_STORAGE', 'track:file://orion_results.json').split(':', maxsplit=1)

    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))

    multiple_of_8 = [8 * i for i in range(32 // 8, 512 // 8)]

    orion.core.cli.main([
        '-vv', '--debug', 'hunt',
        '--config', 'orion.yaml', '-n', 'default_algo', #'--metric', 'error_rate',
        '--max-trials', '10',
        './end_to_end.py', f'--batch-size~choices({multiple_of_8})', '--backend', uri
    ])

    os.chdir(cwd)
    remove('orion_results.json')


def mongodb():

    with subprocess.Popen('mongod --dbpath /tmp/mongodb', stdout=subprocess.DEVNULL, shell=True) as proc:
        while True:
            if proc.poll() is not None:
                break
            else:
                proc.stdout.readline()
                time.sleep(0.01)

        shutil.rmtree('/tmp/mongodb')


if __name__ == '__main__':
    test_orion_poc()
