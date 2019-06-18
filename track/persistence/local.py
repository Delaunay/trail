from typing import Callable

from track.utils.log import error, warning
from track.structure import Project, Trial, TrialGroup
from track.persistence.protocol import Protocol
from track.persistence.storage import load_database, LocalStorage
from track.persistence.utils import parse_uri
from track.containers.types import float32
from track.aggregators.aggregator import Aggregator
from track.aggregators.aggregator import RingAggregator
from track.aggregators.aggregator import StatAggregator
from track.aggregators.aggregator import ValueAggregator
from track.aggregators.aggregator import TimeSeriesAggregator

import time


ring_aggregator = RingAggregator.lazy(10, float32)
stat_aggregator = StatAggregator.lazy(1)
ts_aggregator = TimeSeriesAggregator.lazy()


def _make_container(step, aggregator):
    if step is None:
        if aggregator is None:
            # favor ts aggregator because it has an option to cut the TS for printing purposes
            return ts_aggregator()
        return aggregator()
    else:
        return dict()


class FileProtocol(Protocol):

    def __init__(self, uri):
        uri = parse_uri(uri)

        # file:test.json
        path = uri.get('path')

        if not path:
            # file://test.json
            path = uri.get('address')

        self.storage: LocalStorage = load_database(path)
        self.chronos = {}

    def log_trial_start(self, trial):
        acc = ValueAggregator()
        trial.chronos['runtime'] = acc
        self.chronos['runtime'] = time.time()

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        start_time = self.chronos['runtime']
        acc = trial.chronos['runtime']
        acc.append(time.time() - start_time)

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        for k, v in kwargs.items():
            container = trial.metadata.get(k)

            if container is None:
                container = _make_container(None, aggregator)
                trial.metadata[k] = container

            container.append(v)

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        agg = trial.chronos.get(name)
        if agg is None:
            agg = aggregator()
            trial.chronos[name] = agg

        self.chronos[name] = time.time()

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        start_time = self.chronos[name]
        acc = trial.chronos[name]
        acc.append(time.time() - start_time)

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        for k, v in kwargs.items():
            container = trial.metrics.get(k)

            if container is None:
                container = _make_container(step, aggregator)
                trial.metrics[k] = container

            if step is not None and isinstance(container, dict):
                container[step] = v
            elif step:
                container.append((step, v))
            else:
                container.append(v)

    def add_trial_tags(self, trial, **kwargs):
        trial.tags.update(kwargs)

    def log_trial_arguments(self, trial, **kwargs):
        trial.parameters.update(kwargs)

    def set_trial_status(self, trial, status, error=None):
        trial.status = status
        if error is not None:
            trial.errors.append(error)

    # Object Creation
    def get_project(self, project: Project):
        return self.storage.objects.get(project.uid)

    def new_project(self, project: Project):
        if project.uid in self.storage.objects:
            error(f'Cannot insert project; (uid: {project.uid}) already exists!')
            return

        self.storage.objects[project.uid] = project
        self.storage.project_names[project.name] = project.uid
        self.storage.projects.add(project.uid)

    def get_trial_group(self, group: TrialGroup):
        return self.storage.objects.get(group.uid)

    def new_trial_group(self, group: TrialGroup):
        if group.uid in self.storage.objects:
            error(f'Cannot insert group; (uid: {group.uid}) already exists!')
            return

        project = self.storage.objects.get(group.project_id)
        assert project is not None, 'Cannot create a group without an associated project'

        project.groups.append(group)

        self.storage.objects[group.uid] = group
        self.storage.groups.add(group.uid)
        self.storage.group_names[group.name] = group.uid

    def get_trial(self, trial: Trial):
        trials = []

        if trial.uid in self.storage.objects:
            trial_hash = trial.hash

            for k, obj in self.storage.objects.items():
                if k.startswith(trial_hash):
                    trials.append(obj)

            return trials
        return None

    def new_trial(self, trial: Trial):
        if trial.uid in self.storage.objects:
            trials = self.get_trial(trial)

            max_rev = 0
            for t in trials:
                max_rev = max(max_rev, t.revision)

            warning(f'Trial was already completed. Increasing revision number (rev={max_rev + 1})')
            trial.revision = max_rev + 1
            trial._hash = None

        self.storage.objects[trial.uid] = trial
        self.storage.trials.add(trial.uid)
        return trial

    def add_project_trial(self, project, trial):
        trial.project_id = project.uid
        project.trials.append(trial)

    def add_group_trial(self, group, trial):
        trial.group_id = group.uid
        group.trials.append(trial.uid)

    def commit(self, file_name_override=None, **kwargs):
        self.storage.commit(file_name_override=file_name_override, **kwargs)
