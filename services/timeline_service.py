from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from database import Signal, Trade, get_session
from services.pnl import query_trades_with_dollar_pnl

logger = logging.getLogger(__name__)


class TimelineService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
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
            trade_list = query_trades_with_dollar_pnl(session, Trade.signal_id == signal_id)
            if trade_list:
                trade, pnl_val = trade_list[0]
                events.append({
                    "type": "trade_created",
                    "timestamp": trade.created_at.isoformat() if trade.created_at else None,
                    "data": {"trade_id": trade.id, "entry": trade.entry, "status": trade.status},
                })
                if trade.closed_at:
                    events.append({
                        "type": "trade_closed",
                        "timestamp": trade.closed_at.isoformat() if trade.closed_at else None,
                        "data": {"pnl": pnl_val, "close_reason": trade.close_reason},
                    })
            return events
        finally:
            session.close()

    def trade_timeline(self, trade_id: int) -> list[dict[str, Any]]:
        session = self.session_factory()
        try:
            trade_list = query_trades_with_dollar_pnl(session, Trade.id == trade_id)
            if not trade_list:
                return []
            trade, pnl_val = trade_list[0]
            events = []
            events.append({
                "type": "trade_created",
                "timestamp": trade.created_at.isoformat() if trade.created_at else None,
                "data": {"symbol": trade.symbol, "side": trade.side, "entry": trade.entry, "status": trade.status},
            })
            if trade.closed_at:
                events.append({
                    "type": "trade_closed",
                    "timestamp": trade.closed_at.isoformat() if trade.closed_at else None,
                    "data": {"pnl": pnl_val, "close_reason": trade.close_reason, "exit_price": trade.exit_price},
                })
            return events
        finally:
            session.close()

    def global_timeline(
        self, limit: int = 50, offset: int = 0,
        event_type: Optional[str] = None,
        symbol: Optional[str] = None,
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
            trades_with_pnl = query_trades_with_dollar_pnl(session)
            trades_with_pnl.sort(key=lambda x: x[0].created_at or datetime.min, reverse=True)
            for t, pnl_val in trades_with_pnl[:limit]:
                if symbol and t.symbol != symbol:
                    continue
                if event_type and event_type not in ("trade", "trade_created", "trade_closed"):
                    continue
                events.append({
                    "type": "trade_created" if t.status == "OPEN" else "trade_closed",
                    "id": t.id,
                    "symbol": t.symbol, "side": t.side, "entry": t.entry,
                    "status": t.status, "pnl": pnl_val,
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
