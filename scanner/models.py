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

    probability_score: float = 0.0
    risk_score: float = 0.0
    confidence_signals: list[str] = field(default_factory=list)
    probability_signals: list[str] = field(default_factory=list)
    risk_signals: list[str] = field(default_factory=list)


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

    intelligence: dict[str, Any] = field(default_factory=dict)
    market_session: str = ""
    btc_trend: str = ""
    fear_greed_label: str = ""
    funding_level: str = ""
