from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class IntelligenceBundle:
    symbol: str

    funding: dict[str, Any] = field(default_factory=dict)
    open_interest: dict[str, Any] = field(default_factory=dict)
    btc_context: dict[str, Any] = field(default_factory=dict)
    fear_greed: dict[str, Any] = field(default_factory=dict)
    news: list[dict[str, Any]] = field(default_factory=list)
    whales: list[dict[str, Any]] = field(default_factory=list)
    market_session: str = ""
    exchange_flow: dict[str, Any] = field(default_factory=dict)
    liquidity_context: dict[str, Any] = field(default_factory=dict)

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def confidence(self) -> float:
        scores = []
        if self.funding:
            scores.append(self.funding.get("risk_score", 0.5))
        if self.open_interest:
            scores.append(self.open_interest.get("strength", 0.5))
        if self.fear_greed:
            scores.append(self.fear_greed.get("confidence", 0.5))
        if self.liquidity_context:
            scores.append(self.liquidity_context.get("score", 0.5))
        if self.exchange_flow:
            scores.append(self.exchange_flow.get("confidence", 0.5))
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 4)

    @property
    def feature_count(self) -> int:
        return sum([
            1 if self.funding else 0,
            1 if self.open_interest else 0,
            1 if self.btc_context else 0,
            1 if self.fear_greed else 0,
            1 if self.news else 0,
            1 if self.whales else 0,
            1 if self.market_session else 0,
            1 if self.exchange_flow else 0,
            1 if self.liquidity_context else 0,
        ])

    @property
    def available_features(self) -> list[str]:
        return [name for name, available in [
            ("funding", bool(self.funding)),
            ("open_interest", bool(self.open_interest)),
            ("btc_context", bool(self.btc_context)),
            ("fear_greed", bool(self.fear_greed)),
            ("news", bool(self.news)),
            ("whales", bool(self.whales)),
            ("market_session", bool(self.market_session)),
            ("exchange_flow", bool(self.exchange_flow)),
            ("liquidity_context", bool(self.liquidity_context)),
        ] if available]
