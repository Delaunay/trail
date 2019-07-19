from uuid import UUID
from typing import Dict
import datetime

from track.chrono import ChronoContext
from track.structure import Project, Trial, TrialGroup, Status, status


class SerializerAspect:
    def to_json(self, obj: any, short=False):
        raise NotImplementedError()


class SerializerUUID(SerializerAspect):
    def to_json(self, obj: UUID, short=False):
        return str(obj)


class SerializerTrial(SerializerAspect):
    def to_json(self, obj: Trial, short=False):
        stat = obj.status

        if not isinstance(stat, dict):
            stat = {
                'value': obj.status.value,
                'name': obj.status.name
            }
        return {
            'dtype': 'trial',
            'uid': to_json(obj.uid),
            'revision': obj.revision,
            'hash': obj.hash,
            'name': obj.name,
            'description': obj.description,
            'version': obj.version,
            'tags': obj.tags,
            'group_id': obj.group_id,
            'project_id': obj.project_id,
            'parameters': to_json(obj.parameters, short),
            'metadata': to_json(obj.metadata, short),
            'metrics': to_json(obj.metrics, short),
            'chronos': to_json(obj.chronos, short),
            'errors': obj.errors,
            'status': stat
        }


class SerializerTrialGroup(SerializerAspect):
    def to_json(self, obj: TrialGroup, short=False):
        return {
            'dtype': 'trial_group',
            'uid': to_json(obj.uid),
            'name': obj.name,
            'description': obj.description,
            'metadata': obj.metadata,
            'project_id': obj.project_id,
            'trials': list(obj.trials)
        }


class SerializerProject(SerializerAspect):
    def to_json(self, obj: Project, short=False):
        return {
            'dtype': 'project',
            'uid': to_json(obj.uid),
            'name': obj.name,
            'description': obj.description,
            'metadata': obj.metadata,
            'trials': [to_json(t, short) for t in obj.trials],
            'groups': [to_json(g, short) for g in obj.groups]
        }


class SerializerChronoContext(SerializerAspect):
    def to_json(self, obj: any, short=False):
        return {}


class SerializerStatus(SerializerAspect):
    def to_json(self, obj: Status, short=False):
        return {
            'name': obj.name,
            'value': obj.value
        }


class SerializerDatetime(SerializerAspect):
    def to_json(self, obj: datetime.datetime, short=False):

        return (obj - datetime.datetime(1970, 1, 1)).total_seconds()


serialization_aspects = {
    UUID: SerializerUUID(),
    Project: SerializerProject(),
    TrialGroup: SerializerTrialGroup(),
    Trial: SerializerTrial(),
    ChronoContext: SerializerChronoContext(),
    Status: SerializerStatus(),
    datetime.datetime: SerializerDatetime()
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


def from_json(obj: Dict[str, any]) -> any:
    if not isinstance(obj, dict):
        return obj

    dtype = obj.get('dtype')

    if dtype == 'project':
        return Project(
            _uid=obj['uid'],
            name=obj['name'],
            description=obj['description'],
            metadata=obj['metadata'],
            groups=set([from_json(g) for g in obj['groups']]),
            trials=set([from_json(t) for t in obj['trials']]),
        )

    elif dtype == 'trial_group':
        return TrialGroup(
            _uid=obj['uid'],
            name=obj['name'],
            description=obj['description'],
            metadata=obj['metadata'],
            trials=set(obj['trials']),
            project_id=obj['project_id']
        )

    elif dtype == 'trial':
        return Trial(
            _hash=obj['hash'],
            revision=obj['revision'],
            name=obj['name'],
            description=obj['description'],
            tags=obj['tags'],
            version=obj['version'],
            group_id=obj['group_id'],
            project_id=obj['project_id'],
            parameters=obj['parameters'],
            metadata=to_json(obj['metadata']),
            metrics=obj['metrics'],
            chronos=obj['chronos'],
            errors=obj['errors'],
            status=status(
                name=obj['status']['name'],
                value=obj['status']['value'])
        )

    return obj
