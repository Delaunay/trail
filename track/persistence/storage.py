import os
import json
from dataclasses import dataclass, field
from typing import Dict, Set
from uuid import UUID

from track.utils.log import error, warning
from track.structure import Project, Trial, TrialGroup
from track.serialization import from_json, to_json


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
