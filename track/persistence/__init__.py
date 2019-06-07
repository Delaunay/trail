from .logger import NoLogLogger
from track.serialization import load_database


def build_logger(backend_name, **kwargs):
    # import inside the if so users do not have to install useless packages
    if backend_name == 'comet_ml':
        from .cometml import CMLLogger

        return CMLLogger(**kwargs)

    return NoLogLogger()


def query(backend_name, file_name=None, **kwargs):
    from track.struct import get_current_trial, get_current_project
    from track.struct import Project, TrialGroup, Trial, Status

    """

    :param backend_name:
        -  comet_ml

    :param kwargs:
        - for comet_ml: workspace, project

    :return:
        - RemoteExperiment()
    """

    if backend_name == 'comet_ml':
        from .cometml import CMLExperiment
        return CMLExperiment(**kwargs)

    if backend_name == 'json':
        # The database is a simple array of json objects
        db = load_database(file_name)
        if len(db.projects) == 1:
            for project in db.projects:
                return project

    project = get_current_project()
    if project is not None:
        return project

    # No defined project make a dummy project
    project = Project()
    project.trials = [get_current_trial()]
    return project
