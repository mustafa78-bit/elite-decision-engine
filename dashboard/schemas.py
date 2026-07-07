from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OverviewResponse(BaseModel):
    engine_status: str
    mode: str
    equity: float
    open_trades: int
    risk_level: str


class StatsResponse(BaseModel):
    total_trades: int
    win_rate: float
    pnl: float
    average_return: float


class PortfolioSummaryResponse(BaseModel):
    equity: float
    exposure: float
    open_positions: int
    available_balance: float


class RiskSummaryResponse(BaseModel):
    risk_status: str
    position_limits: dict[str, Any]
    exposure: dict[str, Any]


class ActivityItem(BaseModel):
    type: str
    description: str
    timestamp: str


class ActivityResponse(BaseModel):
    activities: list[ActivityItem]
