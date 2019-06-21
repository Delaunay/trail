from track.utils.log import warning
from track.persistence.utils import parse_uri


def make_comet_ml(uri):
    # import inside the if so users do not have to install useless packages
    from track.persistence.cometml import CometMLProtocol
    return CometMLProtocol(uri)


def make_local(uri):
    from track.persistence.local import FileProtocol
    return FileProtocol(uri)


def make_socket_protocol(uri):
    from track.persistence.socketed import SocketClient
    return SocketClient(uri)


def make_cockroach_protocol(uri):
    from track.persistence.cockroach import Cockroach
    return Cockroach(uri)


_protocols = {
    '__default__': make_local,
    'file': make_local,
    'cometml': make_comet_ml,
    'socket': make_socket_protocol,
    'cockroach': make_cockroach_protocol
}


# protocol://[username:password@]host1[:port1][,...hostN[:portN]]][/[database][?options]]
def get_protocol(backend_name):
    """ proto://arg """

    arguments = parse_uri(backend_name)
    log = _protocols.get(arguments['scheme'])

    if log is None:
        warning(f'Logger (backend: {backend_name}) was not found!')
        log = _protocols.get('__default__')

    return log(backend_name)


if __name__ == '__main__':

    a = parse_uri('protocol://username:password@host1:port1/database?options=2')
    print(a)

    a = parse_uri('socket://192.128.0.1:8123/database?options=2')
    print(a)

    a = parse_uri('cometml:workspace/project?options=2')
    print(a)

    a = parse_uri('file:test.json')
    print(a)
