from uuid import UUID
from typing import Dict
from track.struct import Project, Trial, TrialGroup


class SerializerAspect:
    def to_json(self, obj: any, short=False):
        raise NotImplementedError()


class SerializerUUID(SerializerAspect):
    def to_json(self, obj: UUID, short=False):
        return str(obj)


class SerializerTrial(SerializerAspect):
    def to_json(self, obj: Trial, short=False):
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
    def to_json(self, obj: TrialGroup, short=False):
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
    def to_json(self, obj: Project, short=False):
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


def from_json(obj: Dict[str, any]) -> any:
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

