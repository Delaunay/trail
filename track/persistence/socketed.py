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


def _check(result):
    if result is False:
        warning('RPC failed')

    return result


class SocketClient(Protocol):
    """ forwards all the local track requests to the track server that execute the requests and send back the results

    """

    # socket://[username:password@]host1[:port1][,...hostN[:portN]]][/[database][?options]]
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
    def __init__(self, backend):
        self.backend = backend
        self.authentication = {}

    # https://stackoverflow.com/questions/48506460/python-simple-socket-client-server-using-asyncio
    def run_server(self, add, port):
        sckt = listen_socket(add, port, backend='ssl')

        loop = asyncio.get_event_loop()
        loop.create_task(asyncio.start_server(self.handle_client, sock=sckt))
        loop.run_forever()

    def exec(self, reader, writer, proc_name, proc, args):
        try:
            answer = proc(**args)

            if answer is None:
                answer = True

            write(writer, answer)

        except Exception:
            error(f'An exception occurred while processing (rpc: {proc_name}) '
                  f'for user f{self.get_username(reader)[0]}')

            error(traceback.format_exc())
            write(writer, False)

    async def handle_client(self, reader, writer):
        running = True
        count = 0

        while running:
            request = await read(reader)
            count += 1

            proc_name = request.pop('__rpc__', None)

            if proc_name is None:
                error(f'Could not process message {request}')
                write(writer, False)
                continue

            elif proc_name == 'authenticate':
                request['reader'] = reader
                self.exec(reader, writer, proc_name, self.authenticate, request)
                continue

            elif not self.is_authenticated(reader):
                error(f'Client is not authenticated cannot execute (proc: {proc_name})')
                write(writer, False)
                continue

            # Forward request to backend
            attr = getattr(self.backend, proc_name)

            if attr is None:
                error(f'{self.backend.__name__} does not implement `{proc_name}`')
                write(writer, False)
                continue

            self.exec(reader, writer, proc_name, attr, request)

    def get_username(self, reader):
        return self.authentication.get(reader)

    def is_authenticated(self, reader):
        return self.authentication.get(reader) is not None

    def authenticate(self, reader, username, password):
        self.authentication[reader] = (username, password)
        return 'authenticated'


def start_track_server(protocol, hostname, port):
    """

    :param protocol: string that represent a backend that implements the track protocol

            FileProtocol: file://report.json            : save using the file protocol (local json file)
            CometML     : cometml://workspace/project   : save through cometml API
            MLFloat     : mlflow://...

    :param hostname : hostname of the server
    :param port     : port to listen for incoming client

    :return:
    """
    from track.persistence import get_protocol

    server = SocketServer(get_protocol(protocol))

    try:
        server.run_server(hostname, port)
    except KeyboardInterrupt as e:
        server.commit()
        raise e
    except Exception as e:
        server.commit()
        raise e
