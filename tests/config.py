import os
from tests.e2e.end_to_end import end_to_end_train
from multiprocessing import Process


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


def multi_client_launch(uri, count):
    try:
        clients = [Process(target=end_to_end_train, args=(uri, ['--uid', str(i)])) for i in range(count)]

        [c.start() for c in clients]

        [c.join() for c in clients]

        codes = [c.exitcode for c in clients]
        print(codes)
        return codes

    except Exception as e:
        raise e
