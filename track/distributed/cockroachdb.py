import os
import time
import subprocess
import traceback
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
    setup. Because we do not have masters only salve can die and if it is the case they can be easily restarted

    """

    def __init__(self, location, addrs, store, temp_dir, join=None):

        self.bin = COCKROACH_BIN.get(os.name)
        self.arguments = [
            'start', '--insecure',
            f'--listen-addr={addrs}',
            f'--external-io-dir={location}',
            f'--store={store}',
            f'--temp-dir={temp_dir}'
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

            except Exception as e:
                error(traceback.format_exc())

    def start(self):
        self._process = Process(target=self._start, args=(self.properties,))
        self._process.start()

    def stop(self):
        self.properties['running'] = False
        self._process.join(timeout=5)
        self._process.terminate()

        # you cant just terminate Popen in the case of cockroachdb
        # you need to kill it with fire
        os.kill(self.properties['pid'], signal.SIGTERM)

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


db = CockRoachDB()
db.start()

time.sleep(20)
for k, v in db.properties.items():
   print(k, v)


db.stop()
