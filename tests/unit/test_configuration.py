from track.configuration import options, none, reset_configuration
import os

wd = os.path.dirname(os.path.realpath(__file__))


class WorkingDir:
    owd = None

    def __init__(self, wd):
        self.wd = wd

    def __enter__(self):
        self.owd = os.getcwd()
        os.chdir(self.wd)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.owd)
        reset_configuration()
        if exc_type is not None:
            raise exc_type


def workind_dir(name):
    return WorkingDir(name)


def pop(d, k):
    if k in d:
        d.pop(k)


def test_config_default():
    """ load configuration file but does not find the value so use the provided default"""
    with workind_dir(wd):
        assert options('config.none', 124) == 124


def test_config_nothing():
    """ load configuration file but does not find the value, no default is found"""

    with workind_dir(wd):
        assert options('config.nothing') is none


def test_config_file():
    """  load configuration file and return the value there """

    with workind_dir(wd):
        assert options('config.something', 124) == 125


def test_config_env():
    """ return the value stored in the environment """

    with workind_dir(wd):
        pop(os.environ, 'TRACK_CONFIG_TEST')
        os.environ['TRACK_CONFIG_TEST'] = '123'
        assert int(options('config.test')) == 123


def test_config_env_override():
    """ return the value stored in the environment """

    with workind_dir(wd):
        pop(os.environ, 'TRACK_CONFIG_SOMETHING2')
        os.environ['TRACK_CONFIG_SOMETHING2'] = '127'
        assert int(options('config.something2')) == 127


if __name__ == '__main__':
    test_config_file()
    test_config_env_override()


