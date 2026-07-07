import logging
import sys

from core.engine import DecisionEngine
from core.validator import StartupValidator
from database import create_tables
from logging_config import setup_logging


def main():

    setup_logging()
    logger = logging.getLogger("app")

    validator = StartupValidator()
    if not validator.run():
        logger.critical("Engine startup validation failed. Exiting.")
        sys.exit(1)

    create_tables()

    logger.info("Elite Decision Engine Started")

    engine = DecisionEngine()

    engine.run()


if __name__ == "__main__":
    main()