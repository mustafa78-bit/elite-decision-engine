from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpenInterest:
    symbol: str
    value: float
    timestamp: int
    change_1h: float = 0.0
    change_24h: float = 0.0


@dataclass(frozen=True)
class OpenInterestResult:
    records: tuple[OpenInterest, ...] = ()
    fetched_at: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

    @property
    def empty(self) -> bool:
        return len(self.records) == 0

    @property
    def latest(self) -> Optional[OpenInterest]:
        if self.records:
            return self.records[-1]
        return None

    def for_symbol(self, symbol: str) -> Optional[OpenInterest]:
        for r in self.records:
            if r.symbol == symbol:
                return r
        return None


def detect_oi_trend(records: list[OpenInterest]) -> dict:
    if len(records) < 2:
        return {"trend": "unknown", "strength": 0.0}

    values = [r.value for r in records]
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    avg_change = sum(changes) / len(changes)
    avg_value = sum(values) / len(values)
    pct_change = (avg_change / avg_value * 100) if avg_value > 0 else 0

    if pct_change > 5:
        trend = "strong_increase"
        strength = min(abs(pct_change) / 10, 1.0)
    elif pct_change > 1:
        trend = "increase"
        strength = 0.5
    elif pct_change < -5:
        trend = "strong_decrease"
        strength = min(abs(pct_change) / 10, 1.0)
    elif pct_change < -1:
        trend = "decrease"
        strength = 0.5
    else:
        trend = "neutral"
        strength = 0.0

    return {
        "trend": trend,
        "strength": round(strength, 2),
        "avg_change_pct": round(pct_change, 2),
        "current_value": values[-1] if values else 0,
    }
