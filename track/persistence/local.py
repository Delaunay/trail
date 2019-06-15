import os
import json
from dataclasses import dataclass, field
from typing import Dict, Set, Callable
from uuid import UUID

from track.chrono import ChronoContext
from track.utils.log import error, warning
from track.structure import Project, Trial, TrialGroup
from track.serialization import from_json, to_json
from track.persistence.protocol import Protocol
from track.containers.types import float32
from track.aggregators.aggregator import Aggregator
from track.aggregators.aggregator import RingAggregator
from track.aggregators.aggregator import StatAggregator
from track.aggregators.aggregator import ValueAggregator
from track.aggregators.aggregator import TimeSeriesAggregator


@dataclass
class LocalStorage:
    # Main storage
    target_file: str = None

    _objects: Dict[UUID, any] = field(default_factory=dict)
    # Indexes
    _projects: Set[UUID] = field(default_factory=set)
    _groups: Set[UUID] = field(default_factory=set)
    _trials: Set[UUID] = field(default_factory=set)
    _project_names: Dict[str, UUID] = field(default_factory=dict)
    _group_names: Dict[str, UUID] = field(default_factory=dict)
    _trial_names: Dict[str, UUID] = field(default_factory=dict)

    @property
    def objects(self) -> Dict[UUID, any]:
        return self._objects

    # Indexes
    @property
    def projects(self) -> Set[UUID]:
        return self._projects

    @property
    def groups(self) -> Set[UUID]:
        return self._groups

    @property
    def trials(self) -> Set[UUID]:
        return self._trials

    @property
    def project_names(self) -> Dict[str, UUID]:
        return self._project_names

    @property
    def group_names(self) -> Dict[str, UUID]:
        return self._group_names

    def commit(self, file_name_override=None, **kwargs):
        if file_name_override is None:
            file_name_override = self.target_file

        if file_name_override is None:
            error('No output file target')
            return None

        # only save top level projects
        objects = []
        for uid in self._projects:
            objects.append(to_json(self._objects[uid]))

        with open(file_name_override, 'w') as output:
            json.dump(objects, output, indent=2)

        print(file_name_override)


def merge_objects(o1, o2):
    if type(o1) != type(o2):
        error('Cannot merge object with same UUID but different type')
        return o1

    if type(o1) == Trial:
        error('Two trials with the same UUID')
        return o1

    if type(o1) == TrialGroup:
        if o1.project_id != o2.project_id:
            error('Cannot merge TrialGroups belonging to different projects')
            return o1

        tag_diff = set(o1.tags).symmetric_difference(set(o2.tags))
        if len(tag_diff):
            error('Cannot merge TrialGroups with inconsistent tags')
            return o1

        for trial in o2.trials:
            o1.trials.append(trial)

        return o1

    if type(o1) == Project:
        tag_diff = set(o1.tags).symmetric_difference(set(o2.tags))
        if len(tag_diff):
            error('Cannot merge Projects with inconsistent tags')
            return o1

        for g in o2.groups:
            o1.groups.append(g)

        for t in o2.trials:
            o1.trials.append(t)

        return o1


def load_database(json_name):
    if not os.path.exists(json_name):
        warning(f'Local Storage was not found at {json_name}')
        return LocalStorage(target_file=json_name)

    with open(json_name, 'r') as file:
        objects = json.load(file)

    db = dict()
    projects = set()
    project_names = dict()
    groups = set()
    group_names = dict()
    trials = set()
    trial_names = dict()

    for item in objects:
        obj = from_json(item)

        if obj.uid in db:
            obj = merge_objects(db[obj.uid], obj)

        db[obj.uid] = obj

        if isinstance(obj, Project):
            projects.add(obj.uid)
            if obj.name in project_names:
                error('Non unique project names are not supported')

            if obj.name is not None:
                project_names[obj.name] = obj.uid

            for trial in obj.trials:
                db[trial.uid] = trial
                trials.add(trial.uid)

        elif isinstance(obj, Trial):
            trials.add(obj.uid)
            if obj.name is not None:
                trial_names[obj.name] = obj.uid

        elif isinstance(obj, TrialGroup):
            groups.add(obj.uid)
            if obj.name is not None:
                group_names[obj.name] = obj.uid

    return LocalStorage(json_name, db, projects, groups, trials, project_names, group_names, trial_names)


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

    def __init__(self, file_name):
        self.storage = load_database(file_name)

    def log_trial_start(self, trial):
        acc = ValueAggregator()
        trial.chronos['runtime'] = acc
        return ChronoContext('runtime', acc)

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        pass

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
        return ChronoContext(name, agg, start_callback=start_callback, end_callback=end_callback)

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        pass

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

    def commit(self, file_name_override, **kwargs):
        self.storage.commit(file_name_override=file_name_override, **kwargs)
