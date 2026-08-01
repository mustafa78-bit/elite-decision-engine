from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ConfidenceBreakdownDTO:
    trend_score: float = 0.0
    volume_score: float = 0.0
    btc_score: float = 0.0
    mtf_score: float = 0.0
    risk_score: float = 0.0
    trend_contribution: float = 0.0
    volume_contribution: float = 0.0
    btc_contribution: float = 0.0
    mtf_contribution: float = 0.0
    risk_contribution: float = 0.0
    final_score: float = 0.0
    confidence: float = 0.0
    decision: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RiskContributionDTO:
    atr: float = 0.0
    volatility_score: float = 0.0
    risk_score: float = 0.0
    penalties: dict[str, float] = field(default_factory=dict)
    atr_impact: str = ""
    volatility_class: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceContributionDTO:
    funding_risk: Optional[dict[str, Any]] = None
    oi_trend: Optional[dict[str, Any]] = None
    confidence: float = 0.0
    feature_count: int = 0
    available_features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MarketContributionDTO:
    symbol: str = ""
    price: float = 0.0
    ema20: float = 0.0
    ema50: float = 0.0
    ema200: float = 0.0
    rsi: float = 50.0
    atr: float = 0.0
    volume_24h: float = 0.0
    volatility_class: str = ""
    regime: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StrategyContributionDTO:
    strategy_name: str = ""
    confidence: float = 0.0
    score: float = 0.0
    signals_count: int = 0
    win_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryContributionDTO:
    total_entries: int = 0
    wins: int = 0
    losses: int = 0
    win_rate_pct: float = 0.0
    total_pnl: float = 0.0
    similar_trades_count: int = 0
    similar_trades_win_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionReasoningDTO:
    signal_id: int = 0
    symbol: str = ""
    side: str = ""
    timeframe: str = ""
    entry_price: float = 0.0
    status: str = ""
    decision: str = ""
    confidence_breakdown: Optional[ConfidenceBreakdownDTO] = None
    risk_contribution: Optional[RiskContributionDTO] = None
    intelligence_contribution: Optional[IntelligenceContributionDTO] = None
    market_contribution: Optional[MarketContributionDTO] = None
    strategy_contribution: Optional[StrategyContributionDTO] = None
    memory_contribution: Optional[MemoryContributionDTO] = None
    human_readable: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for key in ("confidence_breakdown", "risk_contribution", "intelligence_contribution",
                     "market_contribution", "strategy_contribution", "memory_contribution"):
            if isinstance(d.get(key), dict):
                pass
            elif hasattr(getattr(self, key, None), "to_dict"):
                d[key] = getattr(self, key).to_dict()
        return d


@dataclass
class DecisionTimelineDTO:
    signal_id: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    total_duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def add_event(self, event_name: str, detail: Optional[str] = None) -> None:
        self.events.append({
            "event": event_name,
            "timestamp": _now_iso(),
            "detail": detail or "",
        })


@dataclass
class DecisionMetadataDTO:
    signal_id: int = 0
    model_version: str = "1.0"
    engine_version: str = "1.0"
    data_freshness_seconds: int = 0
    total_sources_evaluated: int = 0
    sources_available: int = 0
    sources_unavailable: int = 0
    processing_time_ms: float = 0.0
    explanation_version: str = "2.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionExplanationDTO:
    reasoning: Optional[DecisionReasoningDTO] = None
    timeline: Optional[DecisionTimelineDTO] = None
    metadata: Optional[DecisionMetadataDTO] = None

    def to_dict(self) -> dict[str, Any]:
        d = {}
        for key in ("reasoning", "timeline", "metadata"):
            val = getattr(self, key, None)
            if val is not None:
                d[key] = val.to_dict() if hasattr(val, "to_dict") else asdict(val)
        return d
