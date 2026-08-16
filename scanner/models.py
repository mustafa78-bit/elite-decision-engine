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

    trend_score: float = 0.0
    funding_score: float = 0.0
    oi_score: float = 0.0
    cvd_score: float = 0.0

    # ATR-based stop/target, same formula real trades get (execution/tp_sl.py)
    # -- lets the frontend show a scanner opportunity's suggested levels on
    # the chart without inventing a separate/inconsistent calculation.
    # 0.0 (never a real price) until _enrich_opportunities() computes them.
    stop: float = 0.0
    tp1: float = 0.0
    tp2: float = 0.0


@dataclass
class ScanResult:
    symbol: str
    price: float = 0.0
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
