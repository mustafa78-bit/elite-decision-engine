from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Optional

from database import PaperTrade, Signal, Trade, get_session

logger = logging.getLogger(__name__)


def _dollar_pnl(trade: Trade, paper_trade: PaperTrade | None) -> float:
    qty = float(paper_trade.quantity) if (paper_trade is not None and paper_trade.quantity is not None) else 1.0
    return (trade.pnl or 0.0) * qty


class TimelineService:
    def __init__(self, session_factory: Callable[[], Any] | None = None):
        self.session_factory = session_factory or get_session

    def signal_timeline(self, signal_id: int) -> list[dict[str, Any]]:
        session = self.session_factory()
        try:
            signal = session.query(Signal).filter(Signal.id == signal_id).first()
            if not signal:
                return []
            events = []
            events.append({
                "type": "signal_created",
                "timestamp": signal.created_at.isoformat() if signal.created_at else None,
                "data": {"symbol": signal.symbol, "side": signal.side, "status": signal.status},
            })
            trade = session.query(Trade).filter(Trade.signal_id == signal_id).first()
            if trade:
                events.append({
                    "type": "trade_created",
                    "timestamp": trade.created_at.isoformat() if trade.created_at else None,
                    "data": {"trade_id": trade.id, "entry": trade.entry, "status": trade.status},
                })
                if trade.closed_at:
                    paper_trade = session.query(PaperTrade).filter(PaperTrade.position_id == trade.id).first()
                    events.append({
                        "type": "trade_closed",
                        "timestamp": trade.closed_at.isoformat() if trade.closed_at else None,
                        "data": {"pnl": _dollar_pnl(trade, paper_trade), "close_reason": trade.close_reason},
                    })
            return events
        finally:
            session.close()

    def trade_timeline(self, trade_id: int) -> list[dict[str, Any]]:
        session = self.session_factory()
        try:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                return []
            events = []
            events.append({
                "type": "trade_created",
                "timestamp": trade.created_at.isoformat() if trade.created_at else None,
                "data": {"symbol": trade.symbol, "side": trade.side, "entry": trade.entry, "status": trade.status},
            })
            if trade.closed_at:
                paper_trade = session.query(PaperTrade).filter(PaperTrade.position_id == trade.id).first()
                events.append({
                    "type": "trade_closed",
                    "timestamp": trade.closed_at.isoformat() if trade.closed_at else None,
                    "data": {
                        "pnl": _dollar_pnl(trade, paper_trade),
                        "close_reason": trade.close_reason,
                        "exit_price": trade.exit_price,
                    },
                })
            return events
        finally:
            session.close()

    def global_timeline(
        self, limit: int = 50, offset: int = 0,
        event_type: str | None = None,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        session = self.session_factory()
        try:
            events: list[dict[str, Any]] = []
            signals = session.query(Signal).order_by(Signal.created_at.desc()).limit(limit).all()
            for s in signals:
                if symbol and s.symbol != symbol:
                    continue
                if event_type and event_type != "signal":
                    continue
                events.append({
                    "type": "signal",
                    "id": s.id,
                    "symbol": s.symbol, "side": s.side, "status": s.status,
                    "timestamp": s.created_at.isoformat() if s.created_at else None,
                })
            trade_rows = (
                session.query(Trade, PaperTrade)
                .outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
                .order_by(Trade.created_at.desc())
                .limit(limit)
                .all()
            )
            for t, pt in trade_rows:
                if symbol and t.symbol != symbol:
                    continue
                if event_type and event_type not in ("trade", "trade_created", "trade_closed"):
                    continue
                events.append({
                    "type": "trade_created" if t.status == "OPEN" else "trade_closed",
                    "id": t.id,
                    "symbol": t.symbol, "side": t.side, "entry": t.entry,
                    "status": t.status, "pnl": _dollar_pnl(t, pt),
                    "timestamp": t.created_at.isoformat() if t.created_at else None,
                })
            events.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
            paginated = events[offset:offset + limit]
            return {
                "events": paginated,
                "total": len(events),
                "offset": offset,
                "limit": limit,
            }
        finally:
            session.close()
