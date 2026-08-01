"""Scanner Dashboard DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScannerDashboardDTO:
    symbols_scanned: int
    opportunities_found: int
    top_opportunities: list[dict[str, Any]]
    top_signals: list[str]
    market_summary: dict[str, Any]
    intelligence_summary: dict[str, Any]
    timestamp: str = ""


def opportunity_to_dto(opp: Any) -> dict[str, Any]:
    return {
        "rank": opp.rank,
        "symbol": opp.symbol,
        "side": opp.side,
        "strategy": opp.strategy,
        "score": opp.score,
        "probability": getattr(opp, "probability_score", 0.0),
        "risk_score": getattr(opp, "risk_score", 0.0),
        "confidence": opp.confidence,
        "price": opp.price,
        "signals": opp.signals,
        "features": getattr(opp, "features", {}),
    }
