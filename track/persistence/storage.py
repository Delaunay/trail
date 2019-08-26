import os
import json
from dataclasses import dataclass, field
from typing import Dict, Set
import tempfile
from uuid import UUID

from track.utils.log import error, warning, debug
from track.structure import Project, Trial, TrialGroup
from track.serialization import from_json, to_json
from track.aggregators.aggregator import StatAggregator


_print_warning_once = set()


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

    _old_rev_tags: Dict[str, int] = field(default_factory=dict)

    def get_previous_version_tag(self, obj):
        return self._old_rev_tags.get(obj.uid)

    def get_current_version_tag(self, obj):
        if isinstance(obj, Trial):
            return obj.metadata.get('_update_count', 0)
        else:
            print(obj)
        return None

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
            debug('No output file target')
            return None

        # only save top level projects
        objects = []
        for uid in self._projects:
            objects.append(to_json(self._objects[uid]))

        file_name = tempfile.mktemp('track_uncommitted')

        with open(file_name, 'w') as output:
            json.dump(objects, output, indent=2)

        # mv is kind of atomic so this prevent generating half generated files
        os.rename(file_name, file_name_override)

    def _insert_object(self, obj):
        self._objects[obj.uid] = obj

        if isinstance(obj, Trial):
            self._trials.add(obj.uid)

        elif isinstance(obj, TrialGroup):
            self._groups.add(obj.uid)

        elif isinstance(obj, Project):
            self._projects.add(obj.uid)

    def _update_object(self, obj, new):
        if isinstance(obj, Trial):
            # this is for atomic updates
            obj_oversion = obj.metadata.get('_update_count', 0)
            obj_nversion = new.metadata.get('_update_count', 0)
            self._old_rev_tags[obj.uid] = obj_oversion

            # the object has not changed
            if obj_oversion == obj_nversion:
                return

            if obj_oversion > obj_nversion:
                raise RuntimeError(f'Cannot update object with older version {obj_oversion} > {obj_nversion}!')

            obj.status = new.status
            obj.metrics.update(new.metrics)
            obj.parameters.update(new.parameters)

            # Chrono are special they do not get updated if you are the worker
            for name, val in new.chronos.items():
                chrono = obj.chronos.get(name)

                if chrono is None:
                    obj.chronos[name] = val
                elif isinstance(chrono, StatAggregator):
                    break
                else:
                    chrono.update(val)

        elif isinstance(obj, Project):
            obj.trials.update(set(new.trials))

        elif isinstance(obj, TrialGroup):
            obj.trials.update(set(new.trials))

        obj.name = new.name
        obj.description = new.description
        obj.metadata = new.metadata

    def reload(self, filename=None):
        """Reload storage and discard current objects"""
        if filename is None:
            filename = self.target_file

        new_storage = load_database(filename)

        _objects = new_storage._objects
        _projects = new_storage._projects
        _groups = new_storage._groups
        _trials = new_storage._trials
        _project_names = new_storage._project_names
        _group_names = new_storage._group_names
        _trial_names = new_storage._trial_names

    def smart_reload(self, filename=None):
        """Updates current objects with new data"""
        if filename is None:
            filename = self.target_file

        new_storage = load_database(filename)
        for uid, obj in new_storage.objects.items():
            old_obj = self.objects.get(uid)

            if old_obj is not None:
                self._update_object(old_obj, obj)
            else:
                self._insert_object(obj)


def load_database(json_name):
    global _print_warning_once

    if json_name is None:
        return LocalStorage()

    if not os.path.exists(json_name):
        if json_name not in _print_warning_once:
            warning(f'Local Storage was not found at {json_name}')
            _print_warning_once.add(json_name)

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
            raise RuntimeError('Should be unreachable!')

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

            for group in obj.groups:
                db[group.uid] = group
                groups.add(group.uid)

        elif isinstance(obj, Trial):
            trials.add(obj.uid)
            if obj.name is not None:
                trial_names[obj.name] = obj.uid

        elif isinstance(obj, TrialGroup):
            groups.add(obj.uid)
            if obj.name is not None:
                group_names[obj.name] = obj.uid

    return LocalStorage(json_name, db, projects, groups, trials, project_names, group_names, trial_names)
