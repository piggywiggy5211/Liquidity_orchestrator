from lib.logger.basic_logger import setup_basic_logging
from lib.logger.loguru_logger import setup_loguru_logger


def setup_logger(log_level: str, debug: bool):
    setup_loguru_logger(log_level_value=log_level, debug=debug)
    setup_basic_logging(log_level_value=log_level)


if __name__ == "__main__":
    # for debugging
    setup_logger(log_level="INFO", debug=True)

    import logging

    from loguru import logger

    logger.info("Hello World!")
    logging.info("Hello World!")
    try:
        a = 123455
        b = 0
        c = a / b
    except Exception as e:
        logger.exception(e)
        logging.exception(e)
