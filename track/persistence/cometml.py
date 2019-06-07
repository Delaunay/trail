from track.persistence.logger import LoggerBackend
from track.persistence.query import RemoteExperiment, RemoteTrial
from track.struct import Status
from track.utils.log import warning

from collections import defaultdict
from typing import List, Dict
from argparse import Namespace

from comet_ml import Experiment
from comet_ml.api import APIExperiment
from comet_ml import API


class CMLLogger(LoggerBackend):
    def __init__(self, workspace, project_name):
        self.exp = Experiment(
            project_name=project_name,
            workspace=workspace,
            log_code=False         # their log_code sucks
        )
        self.silence_warnings = set()

    def log_argument(self, k, v):
        self.exp.log_parameter(k, v)

    def log_arguments(self, args: Namespace):
        self.exp.log_parameters(dict(vars(args)))

    def log_metrics(self, step=None, **kwargs):
        for key, value in kwargs.items():
            # Comet does not support a non int step
            s = step
            if step and not isinstance(step, (int, float)):
                if key not in self.silence_warnings:
                    warning(f'CometML: Step (value: "{step}") for (key: "{key}") is not a number; ignoring it')
                    self.silence_warnings.add(key)
                s = None

            self.exp.log_metric(key, value, step=s)

    def log_dict(self, key, metrics, step):
        warning(f'CometML does not support dictionary logging; converting..')
        new_metrics = {}

        for k, v in metrics.items():
            new_metrics[f'{key}_{k}'] = v

        self.log_metrics(step=step, **new_metrics)

    def set_status(self, status, error=None):
        self.exp.log_other('status_code', status.value)
        self.exp.log_other('status_name', status.name)

        if error is not None:
            self.exp.log_other('errors', error)

    def log_metadata(self, **kwargs):
        for key, value in kwargs.items():
            # Comet does not support a lot of types
            if not isinstance(value, (int, float, str)):
                value = str(value)

            self.exp.log_other(key, value)

    def set_project(self, project):
        self.exp.log_other('project_id', project)

    def set_group(self, group):
        self.exp.log_other('group_id', group)

    def add_tag(self, key, value):
        self.exp.log_other(f'tag_{key}', value)

    def __getattr__(self, item):
        """ try to use the backend attributes if not available """

        # Look for the attribute in the top level logger
        if hasattr(self.exp, item):
            return getattr(self.exp, item)

        raise AttributeError(item)


class CMLTrial(RemoteTrial):
    def __init__(self, cml_trial: APIExperiment):
        self.trial = cml_trial
        self._other = None
        self._metrics = None

    def _get_metrics(self, key):
        if self._metrics is not None:
            return self._metrics.get(key)

        self._metrics = defaultdict(list)
        for item in self.trial.metrics_raw:
            self._metrics[item['metricName']].append(item)

        return self._metrics.get(key)

    def _get_other(self, key):
        if self._other is not None:
            return self._other.get(key)

        self._other = dict()
        for item in self.trial.other:
            self._other[item['name']] = item

        return self._other.get(key)

    @property
    def metrics(self) -> Dict[any, Dict[any, any]]:
        self._get_metrics(None)
        return self.trial._metrics

    @property
    def status(self) -> Status:
        return Status(self._get_other('status_code'))


class CMLExperiment(RemoteExperiment):
    def __init__(self, workspace, project):
        self.workspace = workspace
        self.project = project
        self.cml_api = API()
        trials = self.cml_api.get(workspace=self.workspace, project=self.project)
        self._trials = [CMLTrial(t) for t in trials]

    @property
    def trials(self) -> List[CMLTrial]:
        return self._trials


