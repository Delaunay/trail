import os


def is_travis():
    return bool(os.environ.get('TRAVIS', 0))


def remove(file):
    import os
    try:
        os.remove(file)
        os.remove(f'{file}.lock')
    except Exception:
        pass
