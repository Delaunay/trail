from track.versioning import default_version_hash


def test_version():
    """ dummy test """
    assert default_version_hash() != '666aaaeaad7ea654f29904d66ad81e07fb54af25df5217ff6254e79d28205199'


if __name__ == '__main__':
    test_version()
