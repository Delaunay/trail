from track.structure import Project, TrialGroup, Trial
from track.aggregators.aggregator import Aggregator
from track.aggregators.aggregator import StatAggregator
from track.aggregators.aggregator import ValueAggregator
from typing import Callable, Optional, List

value_aggregator = ValueAggregator.lazy()


class Protocol:
    def log_trial_start(self, trial):
        """See :func:`~track.persistence.protocol.Protocol.log_trial_start`"""
        raise NotImplementedError()

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        """See :func:`~track.persistence.protocol.Protocol.log_trial_finish`"""
        raise NotImplementedError()

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        """See :func:`~track.persistence.protocol.Protocol.log_trial_chrono_start`"""
        raise NotImplementedError()

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        """See :func:`~track.persistence.protocol.Protocol.log_trial_chrono_finish`"""
        raise NotImplementedError()

    def log_trial_arguments(self, trial: Trial, **kwargs):
        """See :func:`~track.persistence.protocol.Protocol.log_trial_argunents`"""
        raise NotImplementedError()

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = value_aggregator, **kwargs):
        """See :func:`~track.persistence.protocol.Protocol.log_trial_metadata`"""
        raise NotImplementedError()

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        """See :func:`~track.persistence.protocol.Protocol.log_trial_metrics`"""
        raise NotImplementedError()

    def set_trial_status(self, trial: Trial, status, error=None):
        """See :func:`~track.persistence.protocol.Protocol.set_trial_status`"""
        raise NotImplementedError()

    def add_trial_tags(self, trial, **kwargs):
        """See :func:`~track.persistence.protocol.Protocol.add_trial_tags`"""
        raise NotImplementedError()

    # Object Creation
    def get_project(self, project: Project) -> Optional[Project]:
        """See :func:`~track.persistence.protocol.Protocol.get_project`"""
        raise NotImplementedError()

    def new_project(self, project: Project):
        """See :func:`~track.persistence.protocol.Protocol.new_project`"""
        raise NotImplementedError()

    def get_trial_group(self, group: TrialGroup) -> Optional[TrialGroup]:
        """See :func:`~track.persistence.protocol.Protocol.get_trial_group`"""
        raise NotImplementedError()

    def new_trial_group(self, group: TrialGroup):
        """See :func:`~track.persistence.protocol.Protocol.new_trial_group`"""
        raise NotImplementedError()

    def add_project_trial(self, project: Project, trial: Trial):
        """See :func:`~track.persistence.protocol.Protocol.add_project_trial`"""
        raise NotImplementedError()

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        """See :func:`~track.persistence.protocol.Protocol.add_group_trial`"""
        raise NotImplementedError()

    def commit(self, **kwargs):
        """See :func:`~track.persistence.protocol.Protocol.commit`"""
        raise NotImplementedError()

    def get_trial(self, trial: Trial) -> List[Trial]:
        """See :func:`~track.persistence.protocol.Protocol.get_trial`"""
        raise NotImplementedError()

    def new_trial(self, trial: Trial):
        """See :func:`~track.persistence.protocol.Protocol.new_trial`"""
        raise NotImplementedError()

    def fetch_trials(self, query) -> List[Trial]:
        """See :func:`~track.persistence.protocol.Protocol.fetch_trials`"""
        raise NotImplementedError()

    def fetch_groups(self, query):
        """See :func:`~track.persistence.protocol.Protocol.fetch_groups`"""
        raise NotImplementedError()

    def fetch_projects(self, query):
        """See :func:`~track.persistence.protocol.Protocol.fetch_projects`"""
        raise NotImplementedError()
