import os
import json
from track.utils.log import warning, info

_config_file = None
_configuration = None
_warning_was_printed = False


def _look_for_configuration(file_name='track.config'):
    config_file = None

    paths = {
        os.path.dirname(os.path.realpath(__file__)),  # location of the current file
        os.getcwd(),                                  # Current working directory
    }

    files = []
    for path in paths:
        file = f'{path}/{file_name}'

        if os.path.exists(file):
            files.append(file)
            config_file = file

    if len(files) > 1:
        warning(f'found multiple configuration file: {", ".join(files)}')
    elif config_file is not None:
        info(f'loading configuration from {config_file}')

    return config_file


def _load_config_file(file):
    global _configuration
    global _warning_was_printed

    if file is None:
        if not _warning_was_printed:
            warning('No configuration file found')
            _warning_was_printed = True
        return

    with open(file, 'r') as cfile:
        _configuration = json.load(cfile)


def find_configuration(file=None):
    global _config_file

    if file is None:
        file = _look_for_configuration()

    _config_file = file
    _load_config_file(file)


def reset_configuration():
    global _configuration
    global _config_file

    _configuration = None
    _config_file = None


# Used to find if a default was provided or not
# we cannot use None because None might the provided default
class _DefaultNone:
    pass


none = _DefaultNone()


def options(key, default=none):
    global _configuration

    if _configuration is None:
        find_configuration()

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
