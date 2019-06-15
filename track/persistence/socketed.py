from track.persistence.protocol import Protocol
from track.structure import Project, TrialGroup, Trial
from track.aggregators.aggregator import Aggregator
from track.aggregators.aggregator import StatAggregator
from typing import Callable
import asyncio
import socket

# socket://username:password@192.168.0.1:8900/file.json
# 1. Authentication
#       client: {
#           'username': something
#           'pubkey': '....'
#       }
#
#       server: {
#           'pubkey': '...'
#           'token': '...'
#       }
#
#       Decrypt Token and use as AES password

class SocketClient(Protocol):
    def __init__(self, username, password, address, port):
        self.socket = socket.create_connection((address, port))
        self.socket.send()


    def init_encryption(self):

        self.socket.send()

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

    async


class SocketServer(Protocol):
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

