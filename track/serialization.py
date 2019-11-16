from uuid import UUID
from typing import Dict
import datetime

from track.chrono import ChronoContext
from track.structure import Project, Trial, TrialGroup, Status, status, CustomStatus
from track.aggregators.aggregator import StatAggregator

from track.persistence.backends.utils import unflatten


class SerializerAspect:
    def from_json(self, obj):
        return obj

    def to_json(self, obj: any, short=False):
        raise NotImplementedError()


class SerializerUUID(SerializerAspect):
    def to_json(self, obj: UUID, short=False):
        return str(obj)


class SerializerTrial(SerializerAspect):
    ignore_short = {'dtype', 'hash', 'uid', 'project_id', 'group_id'}
    ignore_meta = {'_update_count', '_last_change', 'heartbeat'}

    def from_json(self, obj):
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
            chronos={k: from_json(v) for k, v in obj['chronos'].items()},
            errors=obj['errors'],
            status=status(
                name=obj['status']['name'],
                value=obj['status']['value'])
        )

    def to_json(self, obj: Trial, short=False):
        stat = obj.status

        if not isinstance(stat, dict):
            stat = {
                'value': obj.status.value,
                'name': obj.status.name
            }

        trial = {
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
            'parameters': unflatten(to_json(obj.parameters, short)),
            'metadata': to_json(obj.metadata, short),
            'metrics': to_json(obj.metrics, short),
            'chronos': to_json(obj.chronos, short),
            'errors': obj.errors,
            'status': stat
        }

        if short:
            for i in self.ignore_short:
                trial.pop(i, None)

            for i in self.ignore_meta:
                trial['metadata'].pop(i, None)

        return trial


class SerializerTrialGroup(SerializerAspect):
    @staticmethod
    def maybe_unflatten(v):
        if isinstance(v, dict):
            return unflatten(v)
        return v

    def from_json(self, obj):
        return TrialGroup(
            _uid=obj['uid'],
            name=obj['name'],
            description=obj['description'],
            metadata=obj['metadata'],
            trials=set(obj['trials']),
            project_id=obj['project_id']
        )

    def to_json(self, obj: TrialGroup, short=False):
        return {
            'dtype': 'trial_group',
            'uid': to_json(obj.uid),
            'name': obj.name,
            'description': obj.description,
            'metadata': {k: self.maybe_unflatten(v) for k, v in obj.metadata.items()},
            'project_id': obj.project_id,
            'trials': list(obj.trials)
        }


class SerializerProject(SerializerAspect):
    def from_json(self, obj):
        return Project(
            _uid=obj['uid'],
            name=obj['name'],
            description=obj['description'],
            metadata=obj['metadata'],
            groups=set([from_json(g) for g in obj['groups']]),
            trials=set([from_json(t) for t in obj['trials']]),
        )

    def to_json(self, obj: Project, short=False):
        p = {
            'dtype': 'project',
            'uid': to_json(obj.uid),
            'name': obj.name,
            'description': obj.description,
            'metadata': obj.metadata,
            'trials': [to_json(t, short) for t in obj.trials],
            'groups': [to_json(g, short) for g in obj.groups]
        }
        return p


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


class SerializerStatStream(SerializerAspect):
    def from_json(self, obj, short=False):
        return StatAggregator.from_json(obj)


serialization_aspects = {
    UUID: SerializerUUID(),
    Project: SerializerProject(),
    TrialGroup: SerializerTrialGroup(),
    Trial: SerializerTrial(),
    ChronoContext: SerializerChronoContext(),
    Status: SerializerStatus(),
    datetime.datetime: SerializerDatetime(),
    CustomStatus: SerializerStatus()
}

dtype_serialization = {
    'project': serialization_aspects[Project],
    'trial_group': serialization_aspects[TrialGroup],
    'trial': serialization_aspects[Trial],
    'statstream': SerializerStatStream()
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


def from_json(obj: Dict[str, any], dtype=None) -> any:
    if not isinstance(obj, dict):
        return obj

    dtype = obj.get('dtype', dtype)
    if dtype:
        return dtype_serialization[dtype].from_json(obj)

    return obj
