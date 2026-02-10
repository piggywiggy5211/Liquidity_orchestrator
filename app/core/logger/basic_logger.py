import logging

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        minimal_depth_for_getting_original_line = 2
        frame, depth = logging.currentframe(), minimal_depth_for_getting_original_line
        # It’s a dynamic depth adjustment to “skip over” all of logging’s internal machinery
        # and reach the original code that actually called logging.info()
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_basic_logging():
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
