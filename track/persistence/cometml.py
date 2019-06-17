from track.persistence.protocol import Protocol
from track.aggregators.aggregator import Aggregator, StatAggregator
from track.structure import Trial, TrialGroup, Project
from track.utils.log import warning

from typing import Callable
from comet_ml import Experiment, API

import time


class CometMLClient(Protocol):

    # cometml://[username:password@]host1[:port1][,...hostN[:portN]]][/[database][?options]]
    def __init__(self, project_name, workspace):
        self.cml = Experiment(project_name=project_name, workspace=workspace)
        self.chrono = {}
        self._api = None

    @property
    def api(self):
        # only use API if requested
        if self._api is None:
            self._api = API()
        return self._api

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):

        if start_callback is not None:
            start_callback()

        self.chrono[name] = {
            'start': time.time(),
            'cb': end_callback
        }

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            raise exc_type

        data = self.chrono.get(name)
        if data is None:
            return

        cb = data.get('cb')
        if cb is not None:
            cb()

        data['end'] = time.time()
        self.cml.log_metric(f'chrono_{name}', data['end'] - data['start'])

    def log_trial_start(self, trial):
        self.cml.log_other('trial_start', time.time())

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        self.cml.log_other('trial_end', time.time())
        self.cml.end()

        if exc_type is not None:
            raise exc_type

    def log_trial_arguments(self, trial: Trial, **kwargs):
        self.cml.log_parameters(kwargs)

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        for k, v in kwargs.items():
            self.cml.log_other(k, v)

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        self.cml.log_metrics(kwargs, step=step)

    def set_trial_status(self, trial: Trial, status, error=None):
        self.cml.log_other('trial_status_name', status.name)
        self.cml.log_other('trial_status_value', status.value)

    def add_trial_tags(self, trial, **kwargs):
        self.cml.add_tags([f'{k}-{v}'for k, v in kwargs])

    # Object Creation
    def get_project(self, project: Project):
        return self.api.get(workspace=project.uid)

    def new_project(self, project: Project):
        warning('CometML does not expose this functionality')

    def get_trial_group(self, group: TrialGroup):
        return self.api.get(project=group.uid)

    def new_trial_group(self, group: TrialGroup):
        warning('CometML does not expose this functionality')

    def add_project_trial(self, project: Project, trial: Trial):
        warning('CometML does not expose this functionality')

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        warning('CometML does not expose this functionality')

    def commit(self, **kwargs):
        pass

    def get_trial(self, trial: Trial):
        return self.api.get(workspace=trial.project_id, project=trial.group_id, experiment=trial.uid)

    def new_trial(self, trial: Trial):
        warning('CometML does not expose this functionality')
