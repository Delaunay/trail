import os


def is_travis():
    return os.environ.get('TRAVIS', False)
