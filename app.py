import logging
import sys

from core.engine import DecisionEngine
from core.validator import StartupValidator
from database import create_tables

LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)-8s %(message)s"


def main():

    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
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