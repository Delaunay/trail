import uuid


class SerializerAspect:
    def to_json(self, obj, short=False):
        raise NotImplementedError()


class SerializerUUID(SerializerAspect):
    def to_json(self, obj, short=False):
        return str(obj)


serialization_aspects = {
    uuid.UUID: SerializerUUID()
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


