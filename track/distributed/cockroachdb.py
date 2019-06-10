import os
import time
import subprocess
import traceback
import shutil
from multiprocessing import Process, Manager
from track.utils.log import error
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
        os.makedirs(location, exist_ok=True)

        logs = f'{location}/logs'
        temp = f'{location}/tmp'
        external = f'{location}/extern'
        store = location

        self.bin = COCKROACH_BIN.get(os.name)
        self.arguments = [
            'start', '--insecure',
            f'--listen-addr={addrs}',
            f'--external-io-dir={external}',
            f'--store={store}',
            f'--temp-dir={temp}',
            f'--log-dir={logs}'
        ]

        if join is not None:
            self.arguments.append(f'--join={join}')

        hash = COCKROACH_HASH.get(os.name)

        if compute_version([self.bin]) != hash:
            raise RuntimeError('Binary Hashes do not match')

        if self.bin is None:
            raise RuntimeError(f'{os.name} is not supported')

        self.manager: Manager = Manager()
        self.properties = self.manager.dict()
        self.properties['running'] = False
        self.clean_on_exit = clean_on_exit
        self._process: Process = None

    def _start(self, properties):
        kwargs = dict(
            args=[self.bin] + self.arguments,
            stdout=subprocess.PIPE,
            bufsize=1,
            stderr=subprocess.STDOUT
        )

        with subprocess.Popen(**kwargs) as proc:
            try:
                properties['running'] = True
                properties['pid'] = proc.pid

                while properties['running']:
                    if proc.poll() is None:
                        line = proc.stdout.readline().decode('utf-8')
                        if line:
                            self.parse(properties, line)

                # This does not actually close cockroachdb for some reason
                if proc.poll() is None:
                    os.kill(proc.pid, signal.SIGINT)

                if proc.poll() is None:
                    os.kill(proc.pid, signal.SIGTERM)

            except Exception:
                error(traceback.format_exc())

    def start(self, wait=True):
        self._process = Process(target=self._start, args=(self.properties,))
        self._process.start()

        # wait for all the properties to be populated
        if wait:
            while self.properties.get('nodeID') is None:
                time.sleep(0.01)

    def stop(self):
        self.properties['running'] = False
        self._process.join(timeout=5)
        self._process.terminate()

        # you cant just terminate Popen in the case of cockroachdb
        # you need to kill it with fire
        os.kill(self.properties['pid'], signal.SIGTERM)

        if self.clean_on_exit:
            shutil.rmtree(self.location)

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


if __name__ == '__main__':
    db = CockRoachDB(location='/tmp/cockroach', addrs='localhost')
    db.start(wait=True)

    for k, v in db.properties.items():
        print(k, v)

    db.stop()
