from typing import Callable

from track.structure import Project, Trial, TrialGroup
from track.aggregators.aggregator import Aggregator
from track.aggregators.aggregator import StatAggregator


class ProtocolMultiplexer:

    def __init__(self, *backends):
        self.protos = backends

    def log_trial_start(self, trial):
        return [p.log_trial_start(trial) for p in self.protos][-1]

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        return [p.log_trial_finish(trial, exc_type, exc_val, exc_tb) for p in self.protos][-1]

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        return [p.log_trial_chrono_start(trial, name, aggregator, start_callback, end_callback)
                for p in self.protos][-1]

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        return [p.log_trial_chrono_finish(trial, name, exc_type, exc_val, exc_tb) for p in self.protos][-1]

    def log_trial_arguments(self, trial: Trial, **kwargs):
        return [p.log_trial_arguments(trial, **kwargs) for p in self.protos][-1]

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        return [p.log_trial_metadata(trial, aggregator, **kwargs) for p in self.protos][-1]

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        return [p.log_trial_metrics(trial, step, aggregator, **kwargs) for p in self.protos][-1]

    def set_trial_status(self, trial: Trial, status, error=None):
        return [p.set_trial_status(trial, status, error) for p in self.protos][-1]

    def add_trial_tags(self, trial, **kwargs):
        return [p.add_trial_tags(trial, **kwargs) for p in self.protos][-1]

    # Object Creation
    def get_project(self, project: Project):
        return [p.get_project(project) for p in self.protos][-1]

    def new_project(self, project: Project):
        return [p.new_project(project) for p in self.protos][-1]

    def get_trial_group(self, group: TrialGroup):
        return [p.get_trial_group(group) for p in self.protos][-1]

    def new_trial_group(self, group: TrialGroup):
        return [p.new_trial_group(group) for p in self.protos][-1]

    def add_project_trial(self, project: Project, trial: Trial):
        return [p.add_project_trial(project, trial) for p in self.protos][-1]

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        return [p.add_group_trial(group, trial) for p in self.protos][-1]

    def commit(self, **kwargs):
        return [p.commit(**kwargs) for p in self.protos][-1]

    def get_trial(self, trial: Trial):
        return [p.get_trial(trial) for p in self.protos][-1]

    def new_trial(self, trial: Trial):
        return [p.new_trial(trial) for p in self.protos][-1]
