from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any, Optional

from execution.pipeline import TradingSignal

logger = logging.getLogger(__name__)


DIRECTION_BULLISH = "BULLISH"
DIRECTION_BEARISH = "BEARISH"
DIRECTION_NEUTRAL = "NEUTRAL"
DIRECTION_PASS = "PASS"


def normalize_direction(literal_direction: str, side: str) -> str:
    """Normalize literal direction relative to trade side.

    BULLISH = asset is going up, BEARISH = asset is going down.
    If trading SHORT, a bearish market condition supports the trade (making it relative-BULLISH),
    and a bullish market condition opposes the trade (making it relative-BEARISH).

    For side.upper() == 'SHORT': flip BULLISH <-> BEARISH.
    Otherwise (LONG or default): return literal_direction unchanged.
    """
    direction_upper = literal_direction.upper() if literal_direction else DIRECTION_NEUTRAL
    side_upper = side.upper() if side else "LONG"

    if side_upper == "SHORT":
        if direction_upper == DIRECTION_BULLISH:
            return DIRECTION_BEARISH
        elif direction_upper == DIRECTION_BEARISH:
            return DIRECTION_BULLISH

    return direction_upper


@dataclass
class AgentReport:
    agent_name: str
    symbol: str
    direction: str = DIRECTION_NEUTRAL
    confidence: float = 0.0
    score: float = 0.0
    reasoning: list[str] = field(default_factory=list)
    data_points: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def summary(self) -> str:
        return (
            f"[{self.agent_name}] {self.symbol}: {self.direction} "
            f"(score={self.score:.2f}, confidence={self.confidence:.2f})"
        )


class BaseAgent(ABC):
    def __init__(self, name: str, weight: float = 1.0, priority: int = 5, is_directional: bool = True):
        self.name = name
        self.weight = weight
        self.priority = priority
        self.is_directional = is_directional
        self._eval_count = 0
        self._error_count = 0
        self._total_latency = 0.0

    @abstractmethod
    def evaluate(
        self,
        signal: TradingSignal | None = None,
        scores: dict[str, Any] | None = None,
        market_data: Any | None = None,
        **kwargs: Any,
    ) -> AgentReport:
        ...

    def _timed_evaluate(self, *args: Any, **kwargs: Any) -> AgentReport:
        start = time.perf_counter()
        try:
            report = self.evaluate(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            report.latency_ms = round(elapsed, 2)
            self._eval_count += 1
            self._total_latency += elapsed
            return report
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            self._error_count += 1
            logger.exception("Agent %s evaluation failed: %s", self.name, e)
            return AgentReport(
                agent_name=self.name,
                symbol=getattr(kwargs.get("signal"), "symbol", "?"),
                direction=DIRECTION_PASS,
                confidence=0.0,
                score=0.0,
                reasoning=[f"Evaluation error: {e}"],
                latency_ms=round(elapsed, 2),
            )

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "weight": self.weight,
            "priority": self.priority,
            "eval_count": self._eval_count,
            "error_count": self._error_count,
            "avg_latency_ms": round(self._total_latency / max(self._eval_count, 1), 2),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, weight={self.weight})"
