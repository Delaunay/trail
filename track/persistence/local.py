import os
import json
from dataclasses import dataclass, field
from typing import Dict, Set
from uuid import UUID


from track.utils.log import error, warning
from track.structure import Project, Trial, TrialGroup
from track.serialization import from_json, to_json
from track.persistence.storage import Storage


@dataclass
class LocalStorage(Storage):
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

    def commit(self, name=None):
        if name is None:
            name = self.target_file

        if name is None:
            error('No output file target')
            return None

        # only save top level projects
        objects = []
        for uid in self._projects:
            objects.append(to_json(self._objects[uid]))

        with open(name, 'w') as output:
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


class DatabaseManager:
    """ This make the file system usable in a multi process setting
        each sub process will generate partial report in separate files
        and this process will merge them together to make the final report
    """
    running = True

    def run(self, db_name, partial_loc):
        """
            db_name    : location of the main database
            partial_loc: location where the partial reports are generated
        """
        import os
        import time
        from track.utils.throttle import throttled

        main_storage = load_database(db_name)
        persist = throttled(self.persist, every=60)

        while self.running:
            for file in os.listdir(partial_loc):
                if file.endswith(db_name):
                    continue

                partial = load_database(file)
                main_storage = self.merge(main_storage, partial)

                # delete file from the partial directory
                os.remove(file)

            # Save the merged database to FS
            persist(main_storage, db_name)
            time.sleep(0.1)

    def merge(self, main, partial):
        return main

    def persist(self, main, location):
        pass

