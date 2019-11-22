from track.utils.log import warning, debug
from track.persistence.utils import parse_uri
from track.persistence.multiplexer import ProtocolMultiplexer


def make_comet_ml(uri):
    # import inside the if so users do not have to install useless packages
    from track.persistence.cometml import CometMLProtocol
    return CometMLProtocol(uri)


def make_local(uri, strict=True, eager=True):
    from track.persistence.local import FileProtocol
    return FileProtocol(uri, strict, eager)


def make_socket_protocol(uri):
    from track.persistence.socketed import SocketClient
    return SocketClient(uri)


def make_cockroach_protocol(uri):
    from track.persistence.cockroach import Cockroach
    return Cockroach(uri)


def make_mongodb_protocol(uri):
    from track.persistence.mongodb import MongoDB

    return MongoDB(uri)


def make_ephemeral_protocol(uri):
    from track.persistence.backends import EphemeralDB
    from track.persistence.mongodb_like import MongoDBLike

    return MongoDBLike(uri, client_factory=EphemeralDB)


def make_pickled_protocol(uri):
    from track.persistence.backends import PickledDB
    from track.persistence.mongodb_like import MongoDBLike

    return MongoDBLike(uri, client_factory=PickledDB)


def register(name, proto):
    _protocols[name] = proto


_protocols = {
    '__default__': make_local,
    'file': make_local,
    'cometml': make_comet_ml,
    'socket': make_socket_protocol,
    'cockroach': make_cockroach_protocol,
    'mongodb': make_mongodb_protocol,
    'ephemeral': make_ephemeral_protocol,
    'pickled': make_pickled_protocol
}


# protocol://[username:password@]host1[:port1][,...hostN[:portN]]][/[database][?options]]
def get_protocol(backend_name):
    """ proto://arg """

    arguments = parse_uri(backend_name)
    log = _protocols.get(arguments['scheme'])

    if log is None:
        warning(f'Logger (backend: {backend_name}) was not found!')
        log = _protocols.get('__default__')

    if log is make_local:
        debug('return local protocol')
        return log(backend_name)
    else:
        debug('return multiplexed protocol')
        # return log(backend_name)

        return ProtocolMultiplexer(
            # Make a file Protocol to log everything in memory as well as remotely
            make_local('file:', strict=False, eager=False),
            log(backend_name)
        )
