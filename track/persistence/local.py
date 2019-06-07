from dataclasses import dataclass, field
from typing import Dict, Set
from uuid import UUID

import json
from track.utils.log import error
from track.struct import Project, Trial, TrialGroup
from track.serialization import from_json


@dataclass
class LocalDatabase:
    # Main storage
    objects: Dict[UUID, any] = field(default_factory=dict)
    # Indexes
    projects: Set[UUID] = field(default_factory=set)
    groups: Set[UUID] = field(default_factory=set)
    trials: Set[UUID] = field(default_factory=set)
    project_names: Dict[str, UUID] = field(default_factory=dict)
    group_names: Dict[str, UUID] = field(default_factory=dict)
    trial_names: Dict[str, UUID] = field(default_factory=dict)


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
        elif isinstance(obj, Trial):
            trials.add(obj.uid)
            if obj.name is not None:
                trial_names[obj.name] = obj.uid
        elif isinstance(obj, TrialGroup):
            groups.add(obj.uid)
            if obj.name is not None:
                group_names[obj.name] = obj.uid

    return LocalDatabase(objects, projects, groups, trials, project_names, group_names, trial_names)


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

