"""WebSocket event types and serializers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------
# Market
# ------------------------------------------------------------------

@dataclass
class MarketPayload:
    price: float = 0.0
    regime: str = "NONE"
    btc_health_score: float = 0.0
    volatility: float = 0.0


@dataclass
class MarketEvent:
    event: str = "MARKET_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: MarketPayload = field(default_factory=MarketPayload)


# ------------------------------------------------------------------
# Signal
# ------------------------------------------------------------------

@dataclass
class SignalPayload:
    id: int = 0
    symbol: str = ""
    side: str = ""
    confidence: float = 0.0
    decision: str = "REJECT"
    final_score: float = 0.0


@dataclass
class SignalEvent:
    event: str = "SIGNAL_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: SignalPayload = field(default_factory=SignalPayload)


# ------------------------------------------------------------------
# Risk
# ------------------------------------------------------------------

@dataclass
class RiskPayload:
    risk_score: float = 0.0
    open_trades: int = 0
    max_open_trades: int = 0
    daily_loss: float = 0.0
    max_daily_loss: float = 0.0


@dataclass
class RiskEvent:
    event: str = "RISK_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: RiskPayload = field(default_factory=RiskPayload)


# ------------------------------------------------------------------
# Trade (backward compatible)
# ------------------------------------------------------------------

@dataclass
class TradePayload:
    trade_id: int | None = None
    symbol: str = ""
    side: str = ""
    entry: float = 0.0
    status: str = ""
    exit_price: float | None = None
    pnl: float | None = None
    close_reason: str | None = None


@dataclass
class TradeEvent:
    event: str = "TRADE_OPENED"
    timestamp: str = field(default_factory=_now)
    payload: TradePayload = field(default_factory=TradePayload)


# ------------------------------------------------------------------
# Price Update (Sprint 35)
# ------------------------------------------------------------------

@dataclass
class PricePayload:
    symbol: str = ""
    price: float = 0.0
    change_24h: float = 0.0
    volume: float = 0.0


@dataclass
class PriceUpdateEvent:
    event: str = "PRICE_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: PricePayload = field(default_factory=PricePayload)


# ------------------------------------------------------------------
# Candle Update (Sprint 35)
# ------------------------------------------------------------------

@dataclass
class CandlePayload:
    symbol: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    timestamp: int = 0


@dataclass
class CandleUpdateEvent:
    event: str = "CANDLE_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: CandlePayload = field(default_factory=CandlePayload)


# ------------------------------------------------------------------
# Volume Update (Sprint 35)
# ------------------------------------------------------------------

@dataclass
class VolumePayload:
    symbol: str = ""
    volume_24h: float = 0.0


@dataclass
class VolumeUpdateEvent:
    event: str = "VOLUME_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: VolumePayload = field(default_factory=VolumePayload)


# ------------------------------------------------------------------
# Analytics (Block B)
# ------------------------------------------------------------------

@dataclass
class AnalyticsPayload:
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    monthly_pnl: float = 0.0
    total_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    open_trades: int = 0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0


@dataclass
class AnalyticsEvent:
    event: str = "ANALYTICS_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: AnalyticsPayload = field(default_factory=AnalyticsPayload)


# ------------------------------------------------------------------
# Explanation (Block A)
# ------------------------------------------------------------------

@dataclass
class ExplanationPayload:
    signal_id: int = 0
    decision: str = ""
    confidence: float = 0.0
    breakdown: dict[str, float] = field(default_factory=dict)
    human_readable: str = ""


@dataclass
class ExplanationEvent:
    event: str = "EXPLANATION_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: ExplanationPayload = field(default_factory=ExplanationPayload)


# ------------------------------------------------------------------
# Coordination (Block C)
# ------------------------------------------------------------------

@dataclass
class CoordinationPayload:
    signal_id: int = 0
    consensus_score: float = 0.0
    agreement_level: str = ""
    source_count: int = 0
    recommendation: str = ""
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationEvent:
    event: str = "COORDINATION_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: CoordinationPayload = field(default_factory=CoordinationPayload)


# ------------------------------------------------------------------
# Portfolio (Batch 2)
# ------------------------------------------------------------------

@dataclass
class PortfolioPayload:
    total_pnl: float = 0.0
    open_pnl: float = 0.0
    total_trades: int = 0
    open_trades: int = 0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0


@dataclass
class PortfolioEvent:
    event: str = "PORTFOLIO_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: PortfolioPayload = field(default_factory=PortfolioPayload)


# ------------------------------------------------------------------
# Timeline (Batch 2)
# ------------------------------------------------------------------

@dataclass
class TimelinePayload:
    event_type: str = ""
    event_id: int = 0
    symbol: str = ""
    action: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimelineEvent:
    event: str = "TIMELINE_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: TimelinePayload = field(default_factory=TimelinePayload)


# ------------------------------------------------------------------
# Notification (Batch 2)
# ------------------------------------------------------------------

@dataclass
class NotificationPayload:
    notification_id: int = 0
    event_type: str = ""
    read: bool = False
    summary: str = ""


@dataclass
class NotificationEvent:
    event: str = "NOTIFICATION_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: NotificationPayload = field(default_factory=NotificationPayload)


# ------------------------------------------------------------------
# Preferences (Batch 2)
# ------------------------------------------------------------------

@dataclass
class PreferencesPayload:
    user_id: int = 0
    theme: str = "dark"
    updated_fields: list[str] = field(default_factory=list)


@dataclass
class PreferencesEvent:
    event: str = "PREFERENCES_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: PreferencesPayload = field(default_factory=PreferencesPayload)


# ------------------------------------------------------------------
# Watchlist (Batch 2)
# ------------------------------------------------------------------

@dataclass
class WatchlistPayload:
    watchlist_id: int = 0
    name: str = ""
    symbol_count: int = 0
    action: str = ""


@dataclass
class WatchlistEvent:
    event: str = "WATCHLIST_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: WatchlistPayload = field(default_factory=WatchlistPayload)


# ------------------------------------------------------------------
# Scanner (Epic 4)
# ------------------------------------------------------------------

@dataclass
class ScannerPayload:
    symbol: str = ""
    side: str = ""
    score: float = 0.0
    probability: float = 0.0
    risk_score: float = 0.0
    confidence: float = 0.0
    strategy: str = ""
    signals: list[str] = field(default_factory=list)


@dataclass
class ScannerEvent:
    event: str = "SCANNER_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: ScannerPayload = field(default_factory=ScannerPayload)


# ------------------------------------------------------------------
# Dashboard KPI (Block D)
# ------------------------------------------------------------------

@dataclass
class DashboardPayload:
    widget_type: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardEvent:
    event: str = "DASHBOARD_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: DashboardPayload = field(default_factory=DashboardPayload)


# ------------------------------------------------------------------
# Serializer
# ------------------------------------------------------------------

def serialize(event: Any) -> str:
    return json.dumps(asdict(event))
