import git
import hashlib

from typing import Tuple, List


def get_git_version(module) -> Tuple[str, str]:
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
        with open(file, 'r') as code:
            while True:
                data = code.read(BUF_SIZE)

                if not data:
                    break

                sha256.update(data)

    return sha256.hexdigest()


if __name__ == '__main__':
    print(type(get_file_version(__file__)))

    import benchutils

    print(get_git_version(benchutils))

