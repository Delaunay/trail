import hashlib
import inspect
from typing import Tuple, List


def get_git_version(module) -> Tuple[str, str]:
    import git

    """ This suppose that you did a dev installation of the `module` and that a .git folder is present """
    repo = git.Repo(path=module.__file__, search_parent_directories=True)

    commit_hash = repo.git.rev_parse(repo.head.object.hexsha, short=20)
    commit_date = repo.head.object.committed_datetime

    return commit_hash, commit_date


BUF_SIZE = 65536


def get_file_version(file_name: str) -> str:
    """ hash the file using sha256, used in combination with get_git_version to version non committed modifications """
    return compute_version([file_name])


def compute_version(files: List[str]) -> str:
    sha256 = hashlib.sha256()

    for file in files:
        with open(file, 'rb') as code:
            while True:
                data = code.read(BUF_SIZE)

                if not data:
                    break

                sha256.update(data)

    return sha256.hexdigest()


def compute_hash(*args, **kwargs):
    def encode(item):
        if isinstance(item, str):
            item = item.encode('utf8')
        else:
            item = bytes([item])

        return item

    sha256 = hashlib.sha256()
    for arg in args:
        if arg is None:
            continue

        sha256.update(encode(arg))

    for k, v in kwargs.items():
        if v is None:
            continue

        sha256.update(encode(k))
        sha256.update(encode(v))

    return sha256.hexdigest()


def default_version_hash():
    """ get the current stack frames and from the file compute the version"""
    stack = inspect.stack()
    files = [s.filename for s in stack]
    return compute_version(files)
