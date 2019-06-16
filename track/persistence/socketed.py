from track.persistence.protocol import Protocol
from track.utils.encrypted import open_socket, listen_socket
from track.aggregators.aggregator import Aggregator, StatAggregator
from track.structure import Trial, TrialGroup, Project
from typing import Callable


class SocketClient(Protocol):
    def __init__(self, username, password, address, port):
        self.socket = open_socket(address, port)
        print(self.socket.recvall())


    def log_trial_start(self, trial):
        raise NotImplementedError()

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        raise NotImplementedError()

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        raise NotImplementedError()

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        raise NotImplementedError()

    def log_trial_arguments(self, trial: Trial, **kwargs):
        raise NotImplementedError()

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        raise NotImplementedError()

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        raise NotImplementedError()

    def set_trial_status(self, trial: Trial, status, error=None):
        raise NotImplementedError()

    def add_trial_tags(self, trial, **kwargs):
        raise NotImplementedError()

    # Object Creation
    def get_project(self, project: Project):
        raise NotImplementedError()

    def new_project(self, project: Project):
        raise NotImplementedError()

    def get_trial_group(self, group: TrialGroup):
        raise NotImplementedError()

    def new_trial_group(self, group: TrialGroup):
        raise NotImplementedError()

    def add_project_trial(self, project: Project, trial: Trial):
        raise NotImplementedError()

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        raise NotImplementedError()

    def commit(self, **kwargs):
        raise NotImplementedError()

    def get_trial(self, trial: Trial):
        raise NotImplementedError()

    def new_trial(self, trial: Trial):
        raise NotImplementedError()


class SocketServer(Protocol):

    def run(self, port):
        socket = listen_socket('localhost', port)

        while True:
            client, addr = socket.accept()

            client.sendall(b'HELLO')


        time.sleep(10)


    def log_trial_start(self, trial):
        raise NotImplementedError()

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        raise NotImplementedError()

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        raise NotImplementedError()

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        raise NotImplementedError()

    def log_trial_arguments(self, trial: Trial, **kwargs):
        raise NotImplementedError()

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        raise NotImplementedError()

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        raise NotImplementedError()

    def set_trial_status(self, trial: Trial, status, error=None):
        raise NotImplementedError()

    def add_trial_tags(self, trial, **kwargs):
        raise NotImplementedError()

    # Object Creation
    def get_project(self, project: Project):
        raise NotImplementedError()

    def new_project(self, project: Project):
        raise NotImplementedError()

    def get_trial_group(self, group: TrialGroup):
        raise NotImplementedError()

    def new_trial_group(self, group: TrialGroup):
        raise NotImplementedError()

    def add_project_trial(self, project: Project, trial: Trial):
        raise NotImplementedError()

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        raise NotImplementedError()

    def commit(self, **kwargs):
        raise NotImplementedError()

    def get_trial(self, trial: Trial):
        raise NotImplementedError()

    def new_trial(self, trial: Trial):
        raise NotImplementedError()



if __name__ == '__main__':
    try:
        from multiprocessing import Process
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()

        s = SocketServer()
        server = Process(target=s.run, args=(port,))
        server.start()

        c = SocketClient('', '', 'localhost', port)
    except KeyboardInterrupt as e:
        server.terminate()
        raise e
