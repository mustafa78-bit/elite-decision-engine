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
    volume_change: float = 0.0


@dataclass
class VolumeUpdateEvent:
    event: str = "VOLUME_UPDATE"
    timestamp: str = field(default_factory=_now)
    payload: VolumePayload = field(default_factory=VolumePayload)


# ------------------------------------------------------------------
# Serializer
# ------------------------------------------------------------------

def serialize(event: Any) -> str:
    return json.dumps(asdict(event))
