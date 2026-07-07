import sys

from core.engine import DecisionEngine
from core.validator import StartupValidator
from database import create_tables


def main():

    validator = StartupValidator()
    if not validator.run():
        print("FAILED: Engine startup validation failed. Exiting.")
        sys.exit(1)

    create_tables()

    print("Elite Decision Engine Started")

    engine = DecisionEngine()

    engine.run()


if __name__ == "__main__":
    main()