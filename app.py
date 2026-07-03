from database import create_tables
from core.engine import DecisionEngine


def main():

    create_tables()

    print("🚀 Elite Decision Engine Started")

    engine = DecisionEngine()

    engine.run()


if __name__ == "__main__":
    main()