from track.persistence.utils import parse_uri


def test_uri_parsing():
    hostname = 'localhost'
    port = 8123
    protocol = 'file://test.json'
    password = '123456'
    username = 'root'

    results = parse_uri(f'socket://{username}:{password}@{hostname}:{port}?backend={protocol}&test=2')

    assert results['scheme'] == 'socket'
    assert results['address'] == hostname
    assert results['password'] == password
    assert results['username'] == username
    assert int(results['port']) == port
    assert results['query']['backend'] == protocol
    assert int(results['query']['test']) == 2


if __name__ == '__main__':
    test_uri_parsing()

    a = parse_uri('protocol://username:password@host1:port1/database?options=2')
    print(a)

    a = parse_uri('socket://192.128.0.1:8123/database?options=2')
    print(a)

    a = parse_uri('cometml:workspace/project?options=2')
    print(a)

    a = parse_uri('file:test.json')
    print(a)
