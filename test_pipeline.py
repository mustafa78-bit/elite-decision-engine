"""Simple example for the decision orchestration pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from execution.pipeline import DecisionPipeline


@dataclass(frozen=True)
class ExampleSignal:
    """Minimal signal object accepted by the pipeline."""

    id: int = 1
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    timeframe: str = "1h"


def main() -> None:
    """Run the pipeline once and print the approval result."""

    logging.basicConfig(level=logging.INFO)

    pipeline = DecisionPipeline()
    candidate = pipeline.evaluate(ExampleSignal())

    print("APPROVED" if candidate is not None else "REJECTED")


if __name__ == "__main__":
    main()
