"""

    Implement a Remote Logger.
        Client forwards all the user's request down to the server that executes them one by one.


"""

from track.persistence.protocol import Protocol
from track.persistence.utils import parse_uri
from track.utils import open_socket, listen_socket
from track.aggregators.aggregator import Aggregator, StatAggregator
from track.structure import Trial, TrialGroup, Project
from track.serialization import to_json, from_json
from track.utils.log import error, warning, info

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


class RPCCallFailure(Exception):
    def __init__(self, message, trace=None):
        super(RPCCallFailure, self).__init__(message)


def _check(result):
    if result['status'] != 0:
        error(f'RPC failed with error {result["error"]}')
        raise RPCCallFailure(result['error'], result.get('trace'))

    return from_json(result['return'])


class SocketClient(Protocol):
    """ forwards all the local track requests to the track server that execute the requests and send back the results

    """

    # socket://[username:password@]host1[:port1][,...hostN[:portN]]][/[database][?options]]
    def __init__(self, uri):
        uri = parse_uri(uri)
        self.username = uri.get('username')
        self.password = uri.get('password')
        self.socket = open_socket(uri.get('address'), int(uri.get('port')))

        # Should we send the password hashed ? The connection should be secure regardless
        # Plus how would we handle salting
        kwargs = dict()
        kwargs['__rpc__'] = 'authenticate'
        kwargs['username'] = self.username
        kwargs['password'] = self.password
        send(self.socket, kwargs)
        self.token = _check(recv(self.socket))

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        kwargs = dict()
        kwargs['__rpc__'] = 'log_trial_chrono_start'
        kwargs['trial'] = trial.uid
        kwargs['name'] = name
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        kwargs = dict()
        kwargs['__rpc__'] = 'log_trial_chrono_finish'
        kwargs['trial'] = trial.uid
        kwargs['name'] = name
        kwargs['exc_type'] = None
        kwargs['exc_val'] = None
        kwargs['exc_tb'] = None
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def log_trial_start(self, trial):
        kwargs = dict()
        kwargs['__rpc__'] = 'log_trial_start'
        kwargs['trial'] = trial.uid
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        kwargs = dict()
        kwargs['__rpc__'] = 'log_trial_finish'
        kwargs['trial'] = trial.uid
        kwargs['exc_type'] = None
        kwargs['exc_val'] = None
        kwargs['exc_tb'] = None
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def log_trial_arguments(self, trial: Trial, **kwargs):
        kwargs['__rpc__'] = 'log_trial_arguments'
        kwargs['trial'] = trial.uid
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        kwargs['__rpc__'] = 'log_trial_metadata'
        kwargs['trial'] = trial.uid
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        kwargs['__rpc__'] = 'log_trial_metrics'
        kwargs['trial'] = trial.uid
        kwargs['step'] = step
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def set_trial_status(self, trial: Trial, status, error=None):
        kwargs = dict()
        kwargs['__rpc__'] = 'set_trial_status'
        kwargs['trial'] = trial.uid
        kwargs['status'] = to_json(status)
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def add_trial_tags(self, trial, **kwargs):
        kwargs['__rpc__'] = 'add_trial_tags'
        kwargs['trial'] = trial.uid
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    # Object Creation
    def get_project(self, project: Project):
        kwargs = dict()
        kwargs['__rpc__'] = 'get_project'
        kwargs['project'] = to_json(project)
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def new_project(self, project: Project):
        kwargs = dict()
        kwargs['__rpc__'] = 'new_project'
        kwargs['project'] = to_json(project)
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def get_trial_group(self, group: TrialGroup):
        kwargs = dict()
        kwargs['__rpc__'] = 'get_trial_group'
        kwargs['group'] = to_json(group)
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def new_trial_group(self, group: TrialGroup):
        kwargs = dict()
        kwargs['__rpc__'] = 'new_trial_group'
        kwargs['group'] = to_json(group)
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def add_project_trial(self, project: Project, trial: Trial):
        kwargs = dict()
        kwargs['__rpc__'] = 'add_project_trial'
        kwargs['project'] = to_json(project)
        kwargs['trial'] = to_json(trial)
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        kwargs = dict()
        kwargs['__rpc__'] = 'add_group_trial'
        kwargs['group'] = to_json(group)
        kwargs['trial'] = to_json(trial)
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def commit(self, **kwargs):
        kwargs['__rpc__'] = 'commit'
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def get_trial(self, trial: Trial):
        kwargs = dict()
        kwargs['__rpc__'] = 'get_trail'
        kwargs['trial'] = to_json(trial)
        send(self.socket, kwargs)
        return _check(recv(self.socket))

    def new_trial(self, trial: Trial):
        print(trial)
        kwargs = dict()
        kwargs['__rpc__'] = 'new_trial'
        kwargs['trial'] = to_json(trial)
        print(kwargs)
        send(self.socket, kwargs)
        return _check(recv(self.socket))


async def read(reader, timeout=None):
    data = await (reader.read(4096))

    if not data:
        return None

    size = struct.unpack('I', data[0:4])[0]

    elapsed = 0
    while len(data) < size:
        data += await reader.read(4096)

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
    def __init__(self, uri):
        """

        :param uri:  socket://{hostname}:{port}?backend={protocol} with
                hostname: 127.0.0.1
        """
        from track.persistence import get_protocol

        uri = parse_uri(uri)
        self.address, self.port = uri.get('address'), int(uri.get('port'))
        self.backend = get_protocol(uri['query'].get('backend'))
        self.authentication = {}
        self.timeout = 10

    # https://stackoverflow.com/questions/48506460/python-simple-socket-client-server-using-asyncio
    def run_server(self):
        info(f'Server listening to {self.address}:{self.port}')
        sckt = listen_socket(self.address, self.port)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(asyncio.start_server(self.handle_client, sock=sckt))
        loop.run_forever()

    def process_args(self, args):
        """ replace ids by their object reference so the backend modifies the objects and not a copy"""

        new_args = dict()

        for k, v in args.items():
            if k == 'trial':
                if isinstance(v, str):
                    hashid, rev = v.split('_')
                    v = self.backend.get_trial(Trial(_hash=hashid, revision=rev))
                    print(v)
                    if len(v) == 1:
                        v = v[0]

                v = from_json(v)
                # if isinstance(v, Trial):
                #     a = self.backend.get_trial(v)
                #
                #     if a is not None:
                #         if len(a) == 1:
                #             v = a[0]

            elif k == 'project':
                if isinstance(v, str):
                    v = self.backend.get_project(Project(name=v))

                v = from_json(v)
                # if isinstance(v, Project):
                #     a = self.backend.get_project(v)
                #     if a is not None:
                #         v = a

            elif k == 'group':
                if isinstance(v, str):
                    v = self.backend.get_trial_group(TrialGroup(_uid=v))

                v = from_json(v)
                # if isinstance(v, TrialGroup):
                #     a = self.backend.get_trial_group(v)
                #     if a is not None:
                #         v = a

            new_args[k] = v

        return new_args

    def exec(self, reader, writer, proc_name, proc, args):
        try:
            new_args = self.process_args(args)
            answer = proc(**new_args)

            write(writer, {
                'status': 0,
                'return': to_json(answer)
            })

        except Exception as e:
            error(f'An exception occurred while processing (rpc: {proc_name}) '
                  f'for user {self.get_username(reader)[0]}')

            error(traceback.format_exc())
            write(writer, {
                'status': 1,
                'error': str(e)
            })

    @staticmethod
    async def close_connection(writer):
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def handle_client(self, reader, writer):
        info('Client Connected')
        running = True
        count = 0
        sleep_time = 0

        while running:
            request = await read(reader)
            count += 1

            if request is None:
                time.sleep(0.01)
                sleep_time += 0.01

                if sleep_time > self.timeout:
                    info(f'Client {self.get_username(reader)} is timing out')
                    await self.close_connection(writer)
                    return None
                continue

            proc_name = request.pop('__rpc__', None)
            info(f'Processing Request: {proc_name} for {self.get_username(reader)}')

            if proc_name is None:
                error(f'Could not process message {request}')
                write(writer, {
                    'status': 1,
                    'error': f'Could not process message {request}'
                })
                continue

            elif proc_name == 'authenticate':
                request['reader'] = reader
                self.exec(reader, writer, proc_name, self.authenticate, request)
                continue

            elif not self.is_authenticated(reader):
                error(f'Client is not authenticated cannot execute (proc: {proc_name})')
                write(writer, {
                    'status': 1,
                    'error': f'Client is not authenticated cannot execute (proc: {proc_name})'
                })
                continue

            # Forward request to backend
            attr = getattr(self.backend, proc_name)

            if attr is None:
                error(f'{self.backend.__name__} does not implement `{proc_name}`')
                write(writer, {
                    'status': 1,
                    'error': f'{self.backend.__name__} does not implement `{proc_name}`'
                })
                continue

            self.exec(reader, writer, proc_name, attr, request)
            sleep_time = 0

    def get_username(self, reader):
        usr_pwd = self.authentication.get(reader)
        if usr_pwd is None:
            return None

        return usr_pwd[0]

    def is_authenticated(self, reader):
        return self.authentication.get(reader) is not None

    def authenticate(self, reader, username, password):
        self.authentication[reader] = (username, password)
        return {
            'status': 0,
            'return': True
        }

    def commit(self, **kwargs):
        self.backend.commit(**kwargs)


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
    server = SocketServer(f'socket://{hostname}:{port}?backend={protocol}')

    try:
        server.run_server()
    except KeyboardInterrupt as e:
        server.commit()
        raise e
    except Exception as e:
        server.commit()
        raise e


if __name__ == '__main__':

    start_track_server('file:server_test.json', 'localhost', 37382)

