

def to_json(k: any, short=False):
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


