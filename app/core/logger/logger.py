from app.core.logger.basic_logger import setup_basic_logging
from app.core.logger.loguru_logger import setup_loguru_logger


def setup_logger():
    setup_loguru_logger()
    setup_basic_logging()


if __name__ == "__main__":
    # for debugging
    setup_logger()

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
