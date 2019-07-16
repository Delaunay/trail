import orion.core.cli
from tests.config import is_travis
from multiprocessing import Process
import pytest
import subprocess
import os
import shutil
import time


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_orion_poc(backend='file://orion_results.json'):

    #
    # os.makedirs('/tmp/mongodb', exist_ok=True)
    #
    # server = Process(target=mongodb)
    # server.start()
    #
    # time.sleep(3)

    # out = subprocess.check_output(
    #     'mongo orion_test --eval \'db.createUser({user:"user",pwd:"pass",roles:["readWrite"]});\'',
    #     shell=True
    # )
    # print(out.decode('utf8'))

    multiple_of_8 = [8 * i for i in range(32 // 8, 512 // 8)]

    orion.core.cli.main([
        '-vv', '--debug', 'hunt',
        '--config', 'orion.yaml', '-n', 'default_algo', #'--metric', 'error_rate',
        '--max-trials', '10',
        './end_to_end.py', f'--batch-size~choices({multiple_of_8})', '--backend', backend
    ])

    #  '--batch-size~loguniform(32, 512, discrete=True)'
    # p.kill()


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
