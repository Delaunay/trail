import logging
import sys


def set_log_level(level=logging.INFO):
    trail_logger.setLevel(level)


def get_log_record_constructor():
    old_factory = logging.getLogRecordFactory()

    def log_record(name, level, path, lno, msg, args, exc_info, func=None, sinfo=None, **kwargs):
        start = path.rfind('/track/')
        if start > -1:
            path = path[start + 1:]
        return old_factory(name, level, path, lno, msg, args, exc_info, func, sinfo, **kwargs)

    return log_record


def make_logger(name):
    logger = logging.getLogger(name)
    logger.propagate = False
    logging.setLogRecordFactory(get_log_record_constructor())

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.stream = sys.stdout

    formatter = logging.Formatter(
        '%(relativeCreated)8d [%(levelname)8s] %(name)s [%(process)d] %(pathname)s:%(lineno)d %(message)s')
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(ch)

    return logger


if globals().get('trail_logger') is None:
    trail_logger = make_logger('TRACK')
    set_log_level(logging.DEBUG)


warning = trail_logger.warning
info = trail_logger.info
debug = trail_logger.debug
error = trail_logger.error
critical = trail_logger.critical
exception = trail_logger.exception


