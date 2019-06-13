from .logger import NoLogLogger
from track.utils.log import warning, info
from track.persistence.local import load_database


def make_comet_ml(**kwargs):
    # import inside the if so users do not have to install useless packages
    from .cometml import CMLLogger
    return CMLLogger(**kwargs)


_logger_backend = {
    '__default__': lambda **kwargs: NoLogLogger(),
    'comet_ml': make_comet_ml,
    'local': lambda **kwargs: NoLogLogger(),
}

_protocols = {
    '__default__': load_database,
    'file': load_database,
    'cometml': None,
}


def build_logger(backend_name, **kwargs):
    log = _logger_backend.get(backend_name)

    if log is None:
        warning(f'Logger (backend: {backend_name}) was not found!')
        log = _logger_backend.get('__default__')

    return log(**kwargs)


def register_logger_backend(name, ctor):
    info(f'Registering logger backend {name}')
    _logger_backend[name] = ctor


class ProtocolNotImplemented(BaseException):
    def __init__(self, msg, *args, **kwargs):
        super(self, ProtocolNotImplemented).__init__(*args, **kwargs)
        self.msg = msg


def register_storage_protocol(name, fun):
    info(f'Registering protocol {name}')
    _protocols[name] = fun


def load_storage(backend):
    protocol_name, address = backend.split('://', maxsplit=1)

    proto = _protocols.get(protocol_name)
    if proto is None:
        warning(f'Storage protocol (protocol: {protocol_name}) was not found!')
        proto = _protocols.get('__default__')

    return proto(address)


def query(backend_name, file_name=None, **kwargs):
    """

    :param backend_name:
        -  comet_ml

    :param kwargs:
        - for comet_ml: workspace, project

    :return:
        - RemoteExperiment()
    """

    from track.structure import get_current_trial, get_current_project
    from track.structure import Project

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
