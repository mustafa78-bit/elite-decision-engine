"""CLI entry point for the Elite Decision Engine.

Usage:
    python -m cli status
    python -m cli health
    python -m cli portfolio
    python -m cli trades
    python -m cli performance
"""

from __future__ import annotations

import sys

from cli.commands import COMMANDS


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m cli <command>")
        print(f"Commands: {', '.join(sorted(COMMANDS))}")
        sys.exit(1)

    command = sys.argv[1]

    if command not in COMMANDS:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(sorted(COMMANDS))}")
        sys.exit(1)

    result = COMMANDS[command]()
    print(result)


if __name__ == "__main__":
    main()
