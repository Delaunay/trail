from track.utils.log import warning


def make_comet_ml(**kwargs):
    # import inside the if so users do not have to install useless packages
    from track.persistence.old.cometml import CMLLogger
    return CMLLogger(**kwargs)


def make_local(file_name):
    from track.persistence.local import FileProtocol
    return FileProtocol(file_name)


_protocols = {
    '__default__': make_local,
    'file': make_local,
    'cometml': None,
}


def get_protocol(backend_name):
    """ proto://arg """

    proto, arg = backend_name.split('://', maxsplit=1)
    log = _protocols.get(proto)

    if log is None:
        warning(f'Logger (backend: {backend_name}) was not found!')
        log = _protocols.get('__default__')

    return log(arg)


