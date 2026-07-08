from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_FRESHNESS_THRESHOLD_SECONDS = 3600  # 1 hour

"""
Funding Intelligence — Exchange Integration Points
===================================================

Hyperliquid (REST API):
  - Endpoint: POST https://api.hyperliquid.xyz/info
  - allMids: returns dict of {symbol: mid} — funding rate from mid price
  - fundingHistory: returns list of {fundingRate, time, nextFundingTime, interval}
  - Provider: FundingCollector in market_data/funding/collector.py

Future Exchange Support:
  - Add new collector in market_data/funding/ implementing IntelligenceProvider
  - Register in IntelligenceCollector for unified access
  - Models are exchange-agnostic
"""


@dataclass(frozen=True)
class FundingRate:
    symbol: str
    rate: float
    timestamp: int
    next_funding_time: int
    interval_hours: float = 8.0

    @property
    def annualized_rate(self) -> float:
        return self.rate * (365.25 * 24 / self.interval_hours)

    @property
    def is_positive(self) -> bool:
        return self.rate > 0

    @property
    def is_negative(self) -> bool:
        return self.rate < 0

    def to_score_input(self) -> dict:
        annualized = self.annualized_rate
        score = 1.0
        if annualized > 50 or annualized < -50:
            score = 0.0
        elif annualized > 20 or annualized < -20:
            score = 0.3
        elif annualized > 5 or annualized < -5:
            score = 0.6
        return {
            "funding_rate": round(self.rate, 6),
            "funding_annualized": round(annualized, 4),
            "funding_score": round(score, 2),
            "funding_is_positive": self.is_positive,
        }


@dataclass(frozen=True)
class FundingResult:
    rates: tuple[FundingRate, ...] = ()
    fetched_at: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

    @property
    def empty(self) -> bool:
        return len(self.rates) == 0

    @property
    def latest(self) -> Optional[FundingRate]:
        if self.rates:
            return self.rates[-1]
        return None

    @property
    def is_fresh(self, max_age: float = _FRESHNESS_THRESHOLD_SECONDS) -> bool:
        if not self.rates:
            return False
        latest_ts = self.rates[-1].timestamp
        if latest_ts > 1e12:
            latest_ts = latest_ts / 1000
        age = self.fetched_at - latest_ts
        return age <= max_age

    def rate_for(self, symbol: str) -> Optional[FundingRate]:
        for r in self.rates:
            if r.symbol == symbol:
                return r
        return None


def calculate_funding_trend(rates: list[FundingRate]) -> dict:
    if len(rates) < 2:
        return {"trend": "unknown", "strength": 0.0, "avg_change": 0.0}

    values = [r.annualized_rate for r in rates]
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    avg_change = sum(changes) / len(changes)
    avg_value = sum(values) / len(values)
    pct_change = (avg_change / abs(avg_value) * 100) if avg_value != 0 else 0

    if pct_change > 20:
        trend = "rapid_increase"
        strength = min(abs(pct_change) / 50, 1.0)
    elif pct_change > 5:
        trend = "increasing"
        strength = 0.6
    elif pct_change < -20:
        trend = "rapid_decrease"
        strength = min(abs(pct_change) / 50, 1.0)
    elif pct_change < -5:
        trend = "decreasing"
        strength = 0.6
    else:
        trend = "stable"
        strength = 0.3

    return {
        "trend": trend,
        "strength": round(strength, 2),
        "avg_change_pct": round(pct_change, 2),
        "current_annualized": round(values[-1], 4) if values else 0.0,
        "average_annualized": round(avg_value, 4),
    }


def detect_extreme_funding(rate: FundingRate) -> dict:
    annualized = rate.annualized_rate
    categories = {
        "extreme_positive": annualized > 50,
        "high_positive": 20 < annualized <= 50,
        "elevated_positive": 5 < annualized <= 20,
        "neutral": -5 <= annualized <= 5,
        "elevated_negative": -20 <= annualized < -5,
        "high_negative": -50 <= annualized < -20,
        "extreme_negative": annualized < -50,
    }
    active = [cat for cat, match in categories.items() if match]
    is_extreme = annualized > 50 or annualized < -50
    return {
        "symbol": rate.symbol,
        "annualized_rate": round(annualized, 4),
        "is_extreme": is_extreme,
        "category": active[0] if active else "neutral",
        "warning": "Extreme funding detected" if is_extreme else None,
        "suggestion": "Avoid trading during extreme funding" if is_extreme else None,
    }


def validate_funding_rate(rate: FundingRate) -> list[str]:
    errors: list[str] = []
    if rate.timestamp <= 0:
        errors.append(f"Invalid timestamp for {rate.symbol}: {rate.timestamp}")
    if rate.interval_hours <= 0:
        errors.append(f"Invalid interval for {rate.symbol}: {rate.interval_hours}")
    return errors


def interpret_funding_risk(rate: FundingRate) -> dict:
    annualized = rate.annualized_rate
    if annualized > 50:
        level = "extreme"
        risk_score = 0.0
    elif annualized > 20:
        level = "high"
        risk_score = 0.3
    elif annualized > 5:
        level = "elevated"
        risk_score = 0.6
    elif annualized < -50:
        level = "extreme_negative"
        risk_score = 0.1
    elif annualized < -20:
        level = "high_negative"
        risk_score = 0.3
    elif annualized < -5:
        level = "elevated_negative"
        risk_score = 0.6
    else:
        level = "neutral"
        risk_score = 1.0
    return {
        "symbol": rate.symbol,
        "annualized_rate": round(annualized, 4),
        "level": level,
        "risk_score": round(risk_score, 2),
        "is_positive": rate.is_positive,
    }
