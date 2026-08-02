import asyncio
import logging
import sys

from core.engine import DecisionEngine
from database import create_tables
from logging_config import setup_logging
from startup import StartupValidator


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

    asyncio.run(engine.run())


if __name__ == "__main__":
    main()
