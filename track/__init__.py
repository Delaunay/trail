
from track.client import TrackClient
from track.structure import Project, TrialGroup


def get_git_version(file):
    import git

    """ This suppose that you did a dev installation of the `module` and that a .git folder is present """
    repo = git.Repo(path=file, search_parent_directories=True)

    commit_hash = repo.git.rev_parse(repo.head.object.hexsha, short=20)
    commit_date = repo.head.object.committed_datetime

    return commit_hash, commit_date


__all__ = [
    'TrackClient',
    'Project',
    'TrialGroup',
]


__descr__ = 'Experience tracker'
__version__ = f'0.0.1-{get_git_version(__file__)[0][:8]}'

__license__ = 'BSD-3-Clause'
__author__ = u'Pierre Delaunay'
__author_short__ = u'delaunay'
__author_email__ = 'pierre@delaunay.io'
__copyright__ = u'2019, Delaunay'
__url__ = 'https://github.com/Delaunay/track'
