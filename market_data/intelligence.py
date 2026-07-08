from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from market_data.base import IntelligenceProvider
from market_data.funding.collector import FundingCollector
from market_data.funding.models import interpret_funding_risk
from market_data.open_interest.collector import OpenInterestCollector

logger = logging.getLogger(__name__)

_INTELLIGENCE_FRESHNESS_SECONDS = 3600

FeatureMap = dict[str, Any]


@dataclass(frozen=True)
class MarketFeature:
    symbol: str
    timestamp: int
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)

    def is_fresh(self, now: Optional[float] = None, max_age: float = _INTELLIGENCE_FRESHNESS_SECONDS) -> bool:
        if self.timestamp <= 0:
            return False
        now = now or datetime.now(timezone.utc).timestamp()
        ts = self.timestamp
        if ts > 1e12:
            ts = ts / 1000
        return (now - ts) <= max_age


@dataclass(frozen=True)
class FeatureAvailability:
    funding: bool = False
    open_interest: bool = False
    liquidity: bool = False
    order_flow: bool = False
    whale: bool = False

    @property
    def all_available(self) -> bool:
        return self.funding and self.open_interest

    @property
    def active_features(self) -> list[str]:
        return [name for name, available in [
            ("funding", self.funding),
            ("open_interest", self.open_interest),
            ("liquidity", self.liquidity),
            ("order_flow", self.order_flow),
            ("whale", self.whale),
        ] if available]


class MissingDataHandler:
    FALLBACK_CONFIDENCE = 0.0
    FALLBACK_INT_VALUE = 0
    FALLBACK_FLOAT_VALUE = 0.0
    FALLBACK_STR_VALUE = "unknown"

    @staticmethod
    def safe_float(value: Any, default: float = FALLBACK_FLOAT_VALUE) -> float:
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_int(value: Any, default: int = FALLBACK_INT_VALUE) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_str(value: Any, default: str = FALLBACK_STR_VALUE) -> str:
        if value is None:
            return default
        return str(value)

    @staticmethod
    def safe_dict(value: Any, default: Optional[dict] = None) -> Optional[dict]:
        if isinstance(value, dict):
            return value
        return default


@dataclass(frozen=True)
class IntelligenceBundle:
    symbol: str
    funding_risk: Optional[dict] = None
    oi_trend: Optional[dict] = None
    availability: FeatureAvailability = field(default_factory=FeatureAvailability)
    errors: tuple[str, ...] = ()
    confidence: float = 0.0
    feature_count: int = 0

    @classmethod
    def from_bundle(
        cls,
        symbol: str,
        funding_risk: Optional[dict] = None,
        oi_trend: Optional[dict] = None,
        errors: Optional[list[str]] = None,
    ) -> IntelligenceBundle:
        has_funding = funding_risk is not None
        has_oi = oi_trend is not None
        availability = FeatureAvailability(
            funding=has_funding,
            open_interest=has_oi,
        )
        feature_count = sum([has_funding, has_oi])
        if feature_count == 0:
            confidence = 0.0
        else:
            conf_sum = 0.0
            if has_funding:
                conf_sum += funding_risk.get("risk_score", 1.0) if funding_risk else 0.0
            if has_oi:
                conf_sum += oi_trend.get("strength", 0.5) if oi_trend else 0.0
            confidence = round(conf_sum / feature_count, 2)

        return cls(
            symbol=symbol,
            funding_risk=funding_risk,
            oi_trend=oi_trend,
            availability=availability,
            errors=tuple(errors or []),
            confidence=confidence,
            feature_count=feature_count,
        )


def _log_intelligence_event(symbol: str, event: str, details: Optional[dict] = None) -> None:
    logger.info(
        "Intelligence [%s] %s | symbol=%s details=%s",
        datetime.now(timezone.utc).isoformat(),
        event,
        symbol,
        details or {},
    )


def _log_intelligence_error(symbol: str, source: str, error: str) -> None:
    logger.error(
        "Intelligence [%s] ERROR | symbol=%s source=%s error=%s",
        datetime.now(timezone.utc).isoformat(),
        symbol,
        source,
        error,
    )


class IntelligenceCollector:
    def __init__(
        self,
        funding_collector: Optional[FundingCollector] = None,
        oi_collector: Optional[OpenInterestCollector] = None,
    ):
        self.funding: IntelligenceProvider = funding_collector or FundingCollector()
        self.oi: IntelligenceProvider = oi_collector or OpenInterestCollector()
        _log_intelligence_event("system", "IntelligenceCollector initialized")

    def collect(self, symbol: str) -> IntelligenceBundle:
        errors: list[str] = []
        funding_risk: Optional[dict] = None
        oi_trend: Optional[dict] = None

        try:
            rate = self.funding.fetch_for_symbol(symbol)
            if rate is not None:
                funding_risk = interpret_funding_risk(rate)
                _log_intelligence_event(
                    symbol, "funding_collected",
                    {"risk_level": funding_risk.get("level"), "risk_score": funding_risk.get("risk_score")},
                )
            else:
                errors.append("No funding data available")
                _log_intelligence_event(symbol, "funding_unavailable")
        except Exception as e:
            _log_intelligence_error(symbol, "funding", str(e))
            errors.append(f"Funding error: {e}")

        try:
            oi_data = self.oi.fetch_with_trend(symbol)
            if oi_data.get("value", 0) > 0:
                oi_trend = oi_data
                _log_intelligence_event(
                    symbol, "oi_collected",
                    {"trend": oi_trend.get("trend"), "strength": oi_trend.get("strength")},
                )
            else:
                errors.append("No OI data available")
                _log_intelligence_event(symbol, "oi_unavailable")
        except Exception as e:
            _log_intelligence_error(symbol, "open_interest", str(e))
            errors.append(f"OI error: {e}")

        bundle = IntelligenceBundle.from_bundle(
            symbol=symbol,
            funding_risk=funding_risk,
            oi_trend=oi_trend,
            errors=errors,
        )

        _log_intelligence_event(
            symbol, "collect_complete",
            {
                "features": bundle.feature_count,
                "confidence": bundle.confidence,
                "errors": len(bundle.errors),
            },
        )
        return bundle
