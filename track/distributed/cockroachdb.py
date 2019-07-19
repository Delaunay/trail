import os
import time
import subprocess
import traceback
import shutil

from multiprocessing import Process, Manager

from track.utils.log import error, warning, info, debug
from track.versioning import compute_version

import signal


VERSION = '19.1.1'

COCKROACH_HASH = {
    'posix': '051b9f3afd3478b62e3fce0d140df6f091b4a1e4ef84f05c3f1c3588db2495fa',
    'macos': 'ec1fe3dfb55c67b74c3f04c15d495a55966b930bb378b416a5af5f877fb093de'
}

_base = os.path.dirname(os.path.realpath(__file__))

COCKROACH_BIN = {
    'posix': f'{_base}/cockroach/cockroach_linux',
    'macos': f'{_base}/cockroach/cockroach_macos'
}


class CockRoachDB:
    """ cockroach db is a highly resilient database that allow us to remove the Master in a traditional distributed
    setup.

    This spawn a cockroach node that will store its data in `location`
    """

    def __init__(self, location, addrs, join=None, clean_on_exit=True):
        self.location = location

        logs = f'{location}/logs'
        temp = f'{location}/tmp'
        external = f'{location}/extern'
        store = location

        os.makedirs(logs, exist_ok=True)
        os.makedirs(temp, exist_ok=True)
        os.makedirs(external, exist_ok=True)

        self.location = location
        self.addrs = addrs
        self.bin = COCKROACH_BIN.get(os.name)

        if self.bin is None:
            raise RuntimeError('Your OS is not supported')

        if not os.path.exists(self.bin):
            info('Using system binary')
            self.bin = 'cockroach'
        else:
            hash = COCKROACH_HASH.get(os.name)
            if compute_version([self.bin]) != hash:
                warning('Binary Hashes do not match')

        self.arguments = [
            'start', '--insecure',
            f'--listen-addr={addrs}',
            f'--external-io-dir={external}',
            f'--store={store}',
            f'--temp-dir={temp}',
            f'--log-dir={logs}',
            f'--pid-file={location}/cockroach_pid'
        ]

        if join is not None:
            self.arguments.append(f'--join={join}')

        self.manager: Manager = Manager()
        self.properties = self.manager.dict()
        self.properties['running'] = False
        self.clean_on_exit = clean_on_exit
        self._process: Process = None
        self.cmd = None

    def _start(self, properties):
        kwargs = dict(
            args=' '.join([self.bin] + self.arguments),
            stdout=subprocess.PIPE,
            bufsize=1,
            stderr=subprocess.STDOUT
        )
        self.cmd = kwargs['args']

        with subprocess.Popen(**kwargs, shell=True) as proc:
            try:
                properties['running'] = True
                properties['pid'] = proc.pid

                while properties['running']:
                    if proc.poll() is None:
                        line = proc.stdout.readline().decode('utf-8')
                        if line:
                            self.parse(properties, line)
                    else:
                        properties['running'] = False
                        properties['exit'] = proc.returncode

            except Exception:
                error(traceback.format_exc())

    def start(self, wait=True):
        self._process = Process(target=self._start, args=(self.properties,))
        self._process.start()

        # wait for all the properties to be populated
        if wait:
            while self.properties.get('nodeID') is None and self._process.is_alive():
                time.sleep(0.01)

        self.properties['db_pid'] = int(open(f'{self.location}/cockroach_pid', 'r').read())
        self._setup()

    def _setup(self, client='track_client'):
        out = subprocess.check_output(f'{self.bin} user set {client} --insecure --host={self.addrs}', shell=True)
        debug(out.decode('utf8').strip())

        create_db = f"""
        CREATE DATABASE IF NOT EXISTS track;
        SET DATABASE = track;
        GRANT ALL ON DATABASE track TO {client};
        CREATE TABLE IF NOT EXISTS track.projects (
            uid             BYTES PRIMARY KEY,
            name            STRING,
            description     STRING,
            metadata        JSONB,
            trial_groups    BYTES[],
            trials          BYTES[]
        );
        CREATE TABLE IF NOT EXISTS track.trial_groups (
            uid         BYTES PRIMARY KEY,
            name        STRING,
            description STRING,
            metadata    JSONB,
            trials      BYTES[],
            project_id  BYTES
        );
        CREATE TABLE IF NOT EXISTS track.trials (
            uid         BYTES,
            hash        BYTES,
            revision    SMALLINT,
            name        STRING,
            description STRING,
            tags        JSONB,
            version     BYTES,
            group_id    BYTES,
            project_id  BYTES,
            parameters  JSONB,
            metadata    JSONB,
            metrics     JSONB,
            chronos     JSONB,
            status      JSONB,
            errors      JSONB,

            PRIMARY KEY (hash, revision)
        );""".encode('utf8')

        out = subprocess.check_output(f'{self.bin} sql --insecure --host={self.addrs}', input=create_db, shell=True)
        debug(out.decode('utf8').strip())

    def stop(self):
        self.properties['running'] = False
        self._process.join(timeout=5)
        self._process.terminate()

        os.kill(self.properties['db_pid'], signal.SIGTERM)

        if self.clean_on_exit:
            shutil.rmtree(self.location)

    def wait(self):
        while True:
            time.sleep(0.01)

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        if exc_type is not None:
            raise exc_type

    def parse(self, properties, line):
        if line[0] == '*':
            return
        try:
            a, b = line.split(':', maxsplit=1)
            properties[a.strip()] = b.strip()

        except Exception as e:
            print(e, line, end='\n')
            print(traceback.format_exc())
            raise RuntimeError(f'{line} (cmd: {self.cmd})')

    # properties that are populated once the server has started
    @property
    def node_id(self):
        return self.properties.get('nodeID')

    @property
    def status(self):
        return self.properties.get('status')

    @property
    def sql(self):
        return self.properties.get('sql')

    @property
    def client_flags(self):
        return self.properties.get('client flags')

    @property
    def webui(self):
        return self.properties.get('webui')

    @property
    def build(self):
        return self.properties.get('build')
