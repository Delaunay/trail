import logging


logging.basicConfig(format='[%(levelname)8s] %(name)s [%(process)d] %(pathname)s:%(lineno)d %(message)s')
trail_logger = logging.getLogger('TRACK')


def set_log_level(level=logging.INFO):
    trail_logger.setLevel(level)


warning = trail_logger.warning
info = trail_logger.info
debug = trail_logger.debug
error = trail_logger.error
critical = trail_logger.critical
exception = trail_logger.exception


set_log_level()

