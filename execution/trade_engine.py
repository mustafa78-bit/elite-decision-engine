import logging

from database import get_session, Trade
from execution.tp_sl import TPSLEngine
from notifications.dispatcher import NotificationDispatcher
from notifications.events import TradeEvent


logger = logging.getLogger(__name__)


class TradeEngine:

    def __init__(self):
        self.tp_sl = TPSLEngine()
        self.notifications = NotificationDispatcher()

    def create_trade(
        self,
        signal,
        entry,
        atr,
        intelligence=None,
    ):

        levels = self.tp_sl.calculate(
            entry=entry,
            atr=atr,
            side=signal.side,
        )

        session = get_session()
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

        try:

            trade = Trade(
                signal_id=signal.id,
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

            return trade

        except Exception as e:

            session.rollback()
            logger.error("TRADE CREATE ERROR: %s", e)
            return None

        finally:

            session.close()
