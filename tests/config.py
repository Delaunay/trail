import os


def is_travis():
    return bool(os.environ.get('TRAVIS', 0))
