from __future__ import annotations

import logging
from typing import Any, Optional

from database import Trade, get_session
from execution.tp_sl import TPSLEngine
from notifications.dispatcher import NotificationDispatcher
from notifications.events import TradeEvent

logger = logging.getLogger(__name__)


class TradeEngine:

    def __init__(
        self,
        tp_sl: TPSLEngine | None = None,
        notifications: NotificationDispatcher | None = None,
    ) -> None:
        self.tp_sl = tp_sl or TPSLEngine()
        self.notifications = notifications or NotificationDispatcher()

    def create_trade(
        self,
        signal,
        entry,
        atr,
        intelligence=None,
    ):

        if entry is None or entry == 0:
            logger.warning(
                "Entry is %s for %s %s; trade will use entry=0",
                entry, signal.symbol, signal.side,
            )

        if atr is not None and atr <= 0:
            logger.warning(
                "ATR is %s for %s %s; TPSLEngine will use 1%% of entry as fallback",
                atr, signal.symbol, signal.side,
            )

        session = get_session()
        try:
            levels = self.tp_sl.calculate(
                entry=entry or 0,
                atr=atr or 0,
                side=signal.side,
            )

            existing = (
                session.query(Trade)
                .filter(
                    Trade.signal_id == signal.id,
                    Trade.status == "OPEN",
                )
                .first()
            )

            if existing:
                logger.warning("Trade already exists: %s", signal.symbol)
                return existing

            duplicate = (
                session.query(Trade)
                .filter(
                    Trade.symbol == signal.symbol,
                    Trade.side == signal.side,
                    Trade.status == "OPEN",
                )
                .first()
            )

            if duplicate:
                logger.warning(
                    "Duplicate open trade for same symbol+side: %s %s (existing trade %s)",
                    signal.symbol, signal.side, duplicate.id,
                )
                return None

            trade = Trade(
                signal_id=signal.id,
                user_id=signal.user_id,
                symbol=signal.symbol,
                side=signal.side,
                entry=levels["entry"],
                stop=levels["stop"],
                tp1=levels["tp1"],
                tp2=levels["tp2"],
                rr=levels["rr"],
                status="OPEN",
            )

            session.add(trade)
            session.commit()

            # The trade is already durably committed above -- a failure here
            # (e.g. a non-JSON-serializable intelligence payload, a DB hiccup
            # inside notification persistence) must not make create_trade()
            # return None for a trade that actually exists, which would skip
            # PaperTrade/PaperOrder bookkeeping in ExecutionLoop and silently
            # lose the TRADE_OPENED alert forever. Mirrors the same pattern
            # paper_executor.py's TRADE_CLOSED emit call sites already use.
            try:
                self.notifications.emit(
                    TradeEvent.TRADE_OPENED,
                    {
                        "trade_id": trade.id,
                        "symbol": trade.symbol,
                        "side": trade.side,
                        "entry": trade.entry,
                        "status": trade.status,
                        "intelligence": intelligence or {},
                    },
                )
            except Exception:
                logger.exception("Failed to emit TRADE_OPENED for trade %s", trade.id)

            logger.info(
                "Trade created: id=%s %s %s entry=%s stop=%s tp1=%s rr=%s",
                trade.id, trade.symbol, trade.side,
                trade.entry, trade.stop, trade.tp1, trade.rr,
            )
            return trade

        except Exception as e:

            session.rollback()
            logger.error("Trade creation failed for %s %s: %s", signal.symbol, signal.side, e)
            return None

        finally:

            session.close()
