from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Opportunity:
    symbol: str
    side: str

    strategy: str
    score: float
    confidence: float

    price: float = 0.0
    reason: str = ""
    indicators: dict[str, Any] = field(default_factory=dict)
    features: dict[str, Any] = field(default_factory=dict)
    signals: list[str] = field(default_factory=list)

    rank: int = 0


@dataclass
class ScanResult:
    symbol: str
    trend_score: float = 0.0
    momentum_score: float = 0.0
    breakout_score: float = 0.0
    reversal_score: float = 0.0
    liquidity_score: float = 0.0
    composite_score: float = 0.0
    features: dict[str, Any] = field(default_factory=dict)
    signals: list[str] = field(default_factory=list)
