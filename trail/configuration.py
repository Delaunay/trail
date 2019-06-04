import os
import json
from trail.utils.log import warning

_config_file = None
_configuration = None


def _look_for_configuration(file_name='trail.config'):
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

    _config_file = None


def _load_config_file():
    global _config_file
    global _configuration

    if _config_file is None:
        warning('No configuration file found')
        return

    with open(_config_file, 'r') as cfile:
        _configuration = json.load(cfile)


def options(key, default=None):
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

    if conf is None and default is None:
        warning(f'No configuration found for (key: {key})')

    if conf is None:
        return default

    return conf


if _configuration is None:
    _look_for_configuration()
    _load_config_file()
