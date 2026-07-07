from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class EventType(str, Enum):
    TRADE = "TRADE"
    HEALTH = "HEALTH"
    PORTFOLIO = "PORTFOLIO"


class ServerEvent(BaseModel):
    type: EventType


class TradeEvent(ServerEvent):
    type: EventType = EventType.TRADE
    symbol: str
    side: str
    status: str


class HealthEvent(ServerEvent):
    type: EventType = EventType.HEALTH
    status: str


class PortfolioEvent(ServerEvent):
    type: EventType = EventType.PORTFOLIO
    equity: float
    open_trades: int
