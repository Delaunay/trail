from trail.persistence.logger import LoggerBackend
from argparse import Namespace

from comet_ml import Experiment
from comet_ml import API


class CMLLogger(LoggerBackend):
    def __init__(self, workspace, project_name):
        self.exp = Experiment(project_name, workspace)

    def log_argument(self, k, v):
        self.exp.log_parameter(k, v)

    def log_arguments(self, args: Namespace):
        self.exp.log_parameters(dict(vars(args)))

    def log_metrics(self, step=None, **kwargs):
        for key, value in kwargs.items():
            self.exp.log_metric(key, value, step=step)

    def set_status(self, status, error=None):
        self.exp.log_other('status', status)
        if error is not None:
            self.exp.log_other('errors', error)


class CMLQuery:

    def __init__(self, workspace, project):
        self.workspace = workspace
        self.project = project
        self.cml_api = API()
        self.experiments = self.cml_api.get(self.workspace, self.project)


