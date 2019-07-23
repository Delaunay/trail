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


class Remove:
    def __init__(self, file, nocleanup=False):
        self.file = file
        self.nocleanup = nocleanup

    def __enter__(self):
        if not self.nocleanup:
            remove(self.file)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            remove(self.file)
        else:
            raise
