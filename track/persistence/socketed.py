"""

    Implement a Remote Logger.
        Client forwards all the user's request down to the server that executes them one by one.


"""

from track.persistence.protocol import Protocol
from track.utils.encrypted import open_socket, listen_socket
from track.aggregators.aggregator import Aggregator, StatAggregator
from track.structure import Trial, TrialGroup, Project
from track.serialization import to_json, from_json
from track.utils.log import error, warning
from track.persistence.local import FileProtocol

from typing import Callable

import traceback
import time
import asyncio
import json
import struct


def to_bytes(message) -> bytes:
    return json.dumps(message).encode('utf8')


def to_obj(message: bytes) -> any:
    return from_json(json.loads(message))


def send(socket, msg):
    bytes = to_bytes(msg)
    size = bytearray(struct.pack('I', len(bytes) + 4))
    socket.sendall(size + bytes)


def recv(socket, timeout=None):
    data = socket.recv(4096)
    size = struct.unpack('I', data[0:4])[0]

    elapsed = 0
    while len(data) < size:
        data += socket.recv(4096)

        if len(data) == 0:
            time.sleep(0.01)
            elapsed += 0.01

        if timeout and elapsed > timeout:
            raise TimeoutError('Was not able to receive the entire message in time')

    return to_obj(data[4:])


class SocketClient(Protocol):
    def __init__(self, username, password, address, port):
        self.socket = open_socket(address, port)

        kwargs = dict()
        kwargs['__rpc__'] = 'authenticate'
        kwargs['username'] = username
        kwargs['password'] = password
        send(self.socket, kwargs)
        self.token = recv(self.socket)

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        kwargs = dict()
        kwargs['__rpc__'] = 'chrono_start'
        kwargs['trial'] = trial.uid
        kwargs['name'] = name
        send(self.socket, kwargs)
        return recv(self.socket)

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        kwargs = dict()
        kwargs['__rpc__'] = 'chrono_finish'
        kwargs['trial'] = trial.uid
        kwargs['name'] = name
        kwargs['exc_type'] = None
        kwargs['exc_val'] = None
        kwargs['exc_tb'] = None
        send(self.socket, kwargs)
        return recv(self.socket)

    def log_trial_start(self, trial):
        kwargs = dict()
        kwargs['__rpc__'] = 'trial_start'
        kwargs['trial'] = trial.uid
        send(self.socket, kwargs)
        return recv(self.socket)

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        kwargs = dict()
        kwargs['__rpc__'] = 'trial_finish'
        kwargs['trial'] = trial.uid
        kwargs['exc_type'] = None
        kwargs['exc_val'] = None
        kwargs['exc_tb'] = None
        send(self.socket, kwargs)
        return recv(self.socket)

    def log_trial_arguments(self, trial: Trial, **kwargs):
        kwargs['__rpc__'] = 'log_args'
        kwargs['trial'] = trial.uid
        send(self.socket, kwargs)
        return recv(self.socket)

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        kwargs['__rpc__'] = 'log_meta'
        kwargs['trial'] = trial.uid
        send(self.socket, kwargs)
        return recv(self.socket)

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        kwargs['__rpc__'] = 'log_metrics'
        kwargs['trial'] = trial.uid
        kwargs['step'] = step
        send(self.socket, kwargs)
        return recv(self.socket)

    def set_trial_status(self, trial: Trial, status, error=None):
        kwargs = dict()
        kwargs['__rpc__'] = 'set_status'
        kwargs['trial'] = trial.uid
        kwargs['status'] = to_json(status)
        send(self.socket, kwargs)
        return recv(self.socket)

    def add_trial_tags(self, trial, **kwargs):
        kwargs['__rpc__'] = 'add_tags'
        kwargs['trial'] = trial.uid
        send(self.socket, kwargs)
        return recv(self.socket)

    # Object Creation
    def get_project(self, project: Project):
        kwargs = dict()
        kwargs['__rpc__'] = 'get_project'
        kwargs['project'] = to_json(project)
        send(self.socket, kwargs)
        return recv(self.socket)

    def new_project(self, project: Project):
        kwargs = dict()
        kwargs['__rpc__'] = 'new_project'
        kwargs['project'] = to_json(project)
        send(self.socket, kwargs)
        return recv(self.socket)

    def get_trial_group(self, group: TrialGroup):
        kwargs = dict()
        kwargs['__rpc__'] = 'get_trial_group'
        kwargs['group'] = to_json(group)
        send(self.socket, kwargs)
        return recv(self.socket)

    def new_trial_group(self, group: TrialGroup):
        kwargs = dict()
        kwargs['__rpc__'] = 'trial_start'
        send(self.socket, kwargs)
        return recv(self.socket)

    def add_project_trial(self, project: Project, trial: Trial):
        kwargs = dict()
        kwargs['__rpc__'] = 'add_project_trial'
        kwargs['group'] = to_json(project)
        kwargs['trial'] = to_json(trial)
        send(self.socket, kwargs)
        return recv(self.socket)

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        kwargs = dict()
        kwargs['__rpc__'] = 'add_group_trial'
        kwargs['group'] = to_json(group)
        kwargs['trial'] = to_json(trial)
        send(self.socket, kwargs)
        return recv(self.socket)

    def commit(self, **kwargs):
        kwargs['__rpc__'] = 'commit'
        send(self.socket, kwargs)
        return recv(self.socket)

    def get_trial(self, trial: Trial):
        kwargs = dict()
        kwargs['__rpc__'] = 'get_trail'
        kwargs['trial'] = to_json(trial)
        send(self.socket, kwargs)
        return recv(self.socket)

    def new_trial(self, trial: Trial):
        kwargs = dict()
        kwargs['__rpc__'] = 'new_trial'
        kwargs['trial'] = to_json(trial)
        send(self.socket, kwargs)
        return recv(self.socket)


def read(reader, timeout=None):
    data = reader.read(4096)
    size = struct.unpack('I', data[0:4])[0]

    elapsed = 0
    while len(data) < size:
        data += reader.read(4096)

        if len(data) == 0:
            time.sleep(0.01)
            elapsed += 0.01

        if timeout and elapsed > timeout:
            raise TimeoutError('Was not able to receive the entire message in time')

    return to_obj(data[4:])


def write(writer, msg):
    bytes = to_bytes(msg)
    size = bytearray(struct.pack('I', len(bytes) + 4))
    writer.write(size + bytes)


class SocketServer(Protocol):
    def __init__(self, file_name):
        self.backend = FileProtocol(file_name)

    # https://stackoverflow.com/questions/48506460/python-simple-socket-client-server-using-asyncio
    def run_server(self, add, port):
        sckt = listen_socket(add, port, backend='ssl')

        loop = asyncio.get_event_loop()
        loop.create_task(asyncio.start_server(self.handle_client, sock=sckt))
        loop.run_forever()

    async def handle_client(self, reader, writer):
        running = True
        while running:
            request = await read(reader)

            proc_name = request.pop('__rpc__', None)

            if proc_name is None:
                warning(f'Could not process message {request}')
                continue

            attr = getattr(self, proc_name)
            if attr is None:
                warning(f'SocketServer does not implement `{proc_name}`')
                continue

            try:
                answer = attr(**request)
                if answer is None:
                    answer = True

                write(writer, answer)

            except Exception:
                error(f'An exception occurred while processing (rpc: {proc_name})')
                error(traceback.format_exc())
                write(writer, False)

    def log_trial_start(self, trial):
        return self.backend.log_trial_start(trial)

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        return self.backend.log_trial_finish(trial, exc_type, exc_val, exc_tb)

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        return self.backend.log_trial_chrono_start(trial, name)

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        return self.backend.log_trial_chrono_finish(trial, name, exc_type, exc_val, exc_tb)

    def log_trial_arguments(self, trial: Trial, **kwargs):
        return self.backend.log_trial_arguments(trial, **kwargs)

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        return self.backend.log_trial_metadata(trial, **kwargs)

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        return self.backend.log_trial_metrics(trial, step, **kwargs)

    def set_trial_status(self, trial: Trial, status, error=None):
        return self.backend.set_trial_status(trial, status, error)

    def add_trial_tags(self, trial, **kwargs):
        return self.backend.add_trial_tags(trial, **kwargs)

    # Object Creation
    def get_project(self, project: Project):
        return self.backend.get_project(project)

    def new_project(self, project: Project):
        return self.backend.new_project(project)

    def get_trial_group(self, group: TrialGroup):
        return self.backend.get_trial_group(group)

    def new_trial_group(self, group: TrialGroup):
        return self.backend.new_trial_group(group)

    def add_project_trial(self, project: Project, trial: Trial):
        return self.backend.add_project_trial(project, trial)

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        return self.backend.add_group_trial(group, trial)

    def commit(self, **kwargs):
        return self.backend.commit(**kwargs)

    def get_trial(self, trial: Trial):
        return self.backend.get_trial(trial)

    def new_trial(self, trial: Trial):
        return self.backend.new_trial(trial)


if __name__ == '__main__':
    # try:
    #     from multiprocessing import Process
    #     import socket
    #
    #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     s.bind(('', 0))
    #     port = s.getsockname()[1]
    #     s.close()
    #
    #     s = SocketServer()
    #     server = Process(target=s.run, args=(port,))
    #     server.start()
    #
    #     c = SocketClient('', '', 'localhost', port)
    # except KeyboardInterrupt as e:
    #     server.terminate()
    #     raise e

    print(to_bytes(True))
