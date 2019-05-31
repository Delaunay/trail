from trail.persistence.logger import LoggerBackend
from trail.utils.log import warning
from argparse import Namespace

from comet_ml import Experiment
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

    def log_others(self, **kwargs):
        for key, value in kwargs.items():
            # Comet does not support a lot of types
            if not isinstance(value, (int, float, str)):
                value = str(value)

            self.exp.log_other(key, value)


class CMLQuery:

    def __init__(self, workspace, project):
        self.workspace = workspace
        self.project = project
        self.cml_api = API()
        self.experiments = self.cml_api.get(self.workspace, self.project)



