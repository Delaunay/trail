import os
import json
from track.utils.log import warning

_config_file = None
_configuration = None


def _look_for_configuration(file_name='track.config'):
    global _config_file

    last = __file__.rfind('/')

    paths = {
        __file__[:last],  # location of the current file
        os.getcwd(),      # Current working directory
    }

    files = []
    for path in paths:
        file = f'{path}/{file_name}'

        if os.path.exists(file):
            files.append(file)
            _config_file = file

    if len(files) > 1:
        warning(f'found multiple configuration file: {", ".join(files)}')


def _load_config_file():
    global _config_file
    global _configuration

    if _config_file is None:
        warning('No configuration file found')
        return

    with open(_config_file, 'r') as cfile:
        _configuration = json.load(cfile)


# Used to find if a default was provided or not
# we cannot use None because None might the provided default
class _DefaultNone:
    pass


none = _DefaultNone()


def options(key, default=none):
    global _configuration
    conf = _configuration
    keys = key.split('.')
    env_key = key.replace('.', '_').upper()
    env_key = f'TRAIL_{env_key}'

    env_override = os.environ.get(env_key)
    if env_override is not None:
        warning(f'Found ENV override for {env_key}')
        return env_override

    for k in keys:
        if conf is None:
            break

        conf = conf.get(k)

    if conf is None and default is none:
        warning(f'No configuration found for (key: {key}) and no default was provided')

    if conf is None:
        return default

    return conf


if _configuration is None:
    _look_for_configuration()
    _load_config_file()
