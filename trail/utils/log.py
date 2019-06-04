import logging


logging.basicConfig(format='[%(levelname)s] %(name)s [%(process)d] %(pathname)s:%(lineno)d %(message)s')
trail_logger = logging.getLogger('TRAIL')

warning = trail_logger.warning
info = trail_logger.info
debug = trail_logger.debug
error = trail_logger.error
critical = trail_logger.critical
exception = trail_logger.exception


