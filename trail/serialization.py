from dataclasses import dataclass, field
from typing import Dict, Set
from uuid import UUID

import json
from trail.utils.log import error
from trail.struct import Project, Trial, TrialGroup


class SerializerAspect:
    def to_json(self, obj, short=False):
        raise NotImplementedError()


class SerializerUUID(SerializerAspect):
    def to_json(self, obj, short=False):
        return str(obj)


class SerializerTrial(SerializerAspect):
    def to_json(self, obj, short=False):
        return {
            'dtype': 'trial',
            'uid': to_json(obj.uid),
            'name': obj.name,
            'description': obj.description,
            'tags': obj.tags,
            'group_id': obj.group_id,
            'project_id': obj.project_id,
            'parameters': to_json(obj.parameters, short),
            'metadata': to_json(obj.metadata, short),
            'metrics': to_json(obj.metrics, short),
            'chronos': to_json(obj.chronos, short),
            'errors': obj.errors,
            'status': {
                'value': obj.status.value,
                'name': obj.status.name
            }
        }


class SerializerTrialGroup(SerializerAspect):
    def to_json(self, obj, short=False):
        return {
            'dtype': 'trial_group',
            'uid': to_json(obj.uid),
            'name': obj.name,
            'description': obj.description,
            'tags': obj.tags,
            'project_id': obj.project_id,
            'trials': [to_json(t.uid) for t in obj.trials]
        }


class SerializerProject(SerializerAspect):
    def to_json(self, obj, short=False):
        return {
            'dtype': 'project',
            'uid': to_json(obj.uid),
            'name': obj.name,
            'description': obj.description,
            'tags': obj.tags,
            'trials': [to_json(t, short) for t in obj.trials],
            'groups': [to_json(g, short) for g in obj.groups]
        }


serialization_aspects = {
    UUID: SerializerUUID(),
    Project: SerializerProject(),
    TrialGroup: SerializerTrialGroup(),
    Trial: SerializerTrial()
}


def to_json(k: any, short=False):
    aspect = serialization_aspects.get(type(k))
    if aspect is not None:
        return aspect.to_json(k, short)

    if hasattr(k, 'to_json'):
        try:
            return k.to_json(short)
        except TypeError as e:
            print(type(k))
            raise e

    if isinstance(k, dict):
        return {
            str(k): to_json(v, short) for k, v in k.items()
        }

    return k


def from_json(obj):
    dtype = obj['dtype']
    
    if dtype == 'project':
        return Project(
            uid=obj['uid'],
            name=obj['name'],
            description=obj['description'],
            tags=obj['tags'],
            groups=obj['groups'],
            trials=[t for t in obj['trials']],
        )

    elif dtype == 'trial_group':
        return TrialGroup(
            uid=obj['uid'],
            name=obj['name'],
            description=obj['description'],
            tags=obj['tags'],
            trials=obj['trials'],
            project_id=obj['project_id']
        )

    elif dtype == 'trial':
        return Trial(
            uid=obj['uid'],
            name=obj['name'],
            description=obj['description'],
            tags=obj['tags'],
            group_id=obj['group_id'],
            project_id=obj['project_id'],

            parameters=obj['parameters'],
            metadata=obj['metadata'],
            metrics=obj['metrics'],
            chronos=obj['chronos'],
            errors=obj['errors'],
            status=obj['status']
        )


@dataclass
class LocalDatabase:
    objects: Dict[UUID, any] = field(default_factory=dict)
    projects: Set[UUID] = field(default_factory=set)
    groups: Set[UUID] = field(default_factory=set)
    trials: Set[UUID] = field(default_factory=set)


def load_database(json_name):
    with open(json_name, 'r') as file:
        objects = json.load(file)

    def merge(o1, o2):
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

    db = dict()
    projects = set()
    groups = set()
    trials = set()

    for item in objects:
        obj = from_json(item)

        if obj.uid in db:
            obj = merge(db[obj.uid], obj)

        db[obj.uid] = obj

        if isinstance(obj, Project):
            projects.add(obj.uid)
        elif isinstance(obj, Trial):
            trials.add(obj.uid)
        elif isinstance(obj, TrialGroup):
            groups.add(obj.uid)

    return LocalDatabase(objects, projects, groups, trials)
