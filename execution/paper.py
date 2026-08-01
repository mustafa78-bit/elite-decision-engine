"""Paper trading domain models and executor.

This module adds PaperOrder and PaperTrade tracking on top of the existing
position management from ``execution.paper_executor``. Domain models are
dataclasses; persistence reuses SQLAlchemy models from ``database.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from database import (
    CANCEL,
    CLOSED,
    FILLED,
    OPEN,
    PARTIALLY_FILLED,
    PENDING,
    TAKE_PROFIT,
    STOP_LOSS,
    TP_HIT,
    SL_HIT,
    PaperOrder as PaperOrderModel,
    PaperTrade as PaperTradeModel,
    Trade,
    get_session,
)
from execution.lifecycle import (
    validate_fill_order,
    validate_cancel_order,
    validate_close_trade,
    is_trade_terminal,
)
from execution.paper_executor import PaperExecutor as _PositionExecutor
from execution.paper_executor import TradeMonitorResult


_LEGACY_TO_DOMAIN_STATUS = {
    "TP_HIT": TAKE_PROFIT,
    "SL_HIT": STOP_LOSS,
}


def _domain_status(raw: str) -> str:
    return _LEGACY_TO_DOMAIN_STATUS.get(raw, raw)


@dataclass(frozen=True)
class PaperPosition:
    id: int
    symbol: str
    side: str
    entry: float
    stop_loss: float
    take_profit: float
    take_profit_2: Optional[float]
    pnl: float
    status: str
    exit_price: Optional[float]
    close_reason: Optional[str]
    created_at: Optional[datetime]
    closed_at: Optional[datetime]

    @classmethod
    def from_trade(cls, trade: Trade) -> PaperPosition:
        return cls(
            id=trade.id,
            symbol=str(trade.symbol),
            side=str(trade.side),
            entry=float(trade.entry or 0),
            stop_loss=float(trade.stop or 0),
            take_profit=float(trade.tp1 or 0),
            take_profit_2=float(trade.tp2) if trade.tp2 is not None else None,
            pnl=float(trade.pnl or 0),
            status=_domain_status(str(trade.status or OPEN)),
            exit_price=float(trade.exit_price) if trade.exit_price is not None else None,
            close_reason=str(trade.close_reason) if trade.close_reason is not None else None,
            created_at=trade.created_at,
            closed_at=trade.closed_at,
        )


@dataclass(frozen=True)
class PaperOrder:
    id: int
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    filled_price: Optional[float]
    filled_quantity: Optional[float]
    status: str
    trade_id: Optional[int]
    reason: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_model(cls, model: PaperOrderModel) -> PaperOrder:
        return cls(
            id=model.id,
            symbol=str(model.symbol),
            side=str(model.side),
            order_type=str(model.order_type),
            quantity=float(model.quantity),
            price=float(model.price) if model.price is not None else None,
            filled_price=float(model.filled_price) if model.filled_price is not None else None,
            filled_quantity=float(model.filled_quantity) if model.filled_quantity is not None else None,
            status=str(model.status),
            trade_id=model.trade_id,
            reason=str(model.reason) if model.reason is not None else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


@dataclass(frozen=True)
class PaperTrade:
    id: int
    position_id: int
    order_id: Optional[int]
    symbol: str
    side: str
    entry: float
    exit_price: Optional[float]
    quantity: float
    pnl: float
    status: str
    close_reason: Optional[str]
    created_at: Optional[datetime]
    closed_at: Optional[datetime]

    @classmethod
    def from_model(cls, model: PaperTradeModel) -> PaperTrade:
        return cls(
            id=model.id,
            position_id=model.position_id,
            order_id=model.order_id,
            symbol=str(model.symbol),
            side=str(model.side),
            entry=float(model.entry or 0),
            exit_price=float(model.exit_price) if model.exit_price is not None else None,
            quantity=float(model.quantity or 0),
            pnl=float(model.pnl or 0),
            status=_domain_status(str(model.status or OPEN)),
            close_reason=str(model.close_reason) if model.close_reason is not None else None,
            created_at=model.created_at,
            closed_at=model.closed_at,
        )


class PaperExecutor:
    """Paper trading executor that tracks orders, positions, and trades.

    Delegates position lifecycle to ``execution.paper_executor.PaperExecutor``.
    Adds order tracking (PaperOrder) and per-fill trade records (PaperTrade)
    on top of the existing position management.
    """

    def __init__(
        self,
        position_executor: Optional[_PositionExecutor] = None,
        session_factory: Callable[[], Any] = get_session,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._positions = position_executor or _PositionExecutor()
        self.session_factory = session_factory
        self.logger = logger or logging.getLogger(__name__)

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> Optional[PaperOrder]:
        """Create a pending paper order."""
        session = self.session_factory()
        try:
            order = PaperOrderModel(
                symbol=symbol.upper().strip(),
                side=side.upper().strip(),
                order_type=order_type.upper(),
                quantity=float(quantity),
                price=float(price) if price is not None else None,
                status="PENDING",
                reason=reason,
            )
            session.add(order)
            session.commit()
            session.refresh(order)
            session.expunge(order)
            self.logger.info("Paper order %s placed: %s %s", order.id, symbol, side)
            return PaperOrder.from_model(order)
        except Exception:
            session.rollback()
            self.logger.exception("Failed to place paper order: %s %s", symbol, side)
            return None
        finally:
            session.close()

    def fill_order(
        self,
        order_id: int,
        entry: float,
        stop_loss: float,
        take_profit: float,
        take_profit_2: Optional[float] = None,
        signal_id: Optional[int] = None,
    ) -> Optional[tuple[PaperOrder, PaperPosition, PaperTrade]]:
        """Fill a pending order, creating a position and trade record."""
        session = self.session_factory()
        try:
            order = session.query(PaperOrderModel).filter(PaperOrderModel.id == order_id).first()
            if order is None:
                self.logger.warning("Paper order not found: %s", order_id)
                return None

            validate_fill_order(order.status)

            trade = self._positions.open_trade(
                symbol=order.symbol,
                side=order.side,
                entry=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                signal_id=signal_id,
                take_profit_2=take_profit_2,
            )
            if trade is None:
                return None

            if self._has_open_trade_for_position(session, trade.id):
                self.logger.warning("Duplicate paper trade for position %s", trade.id)
                return None

            order.status = FILLED
            order.filled_price = float(entry)
            order.filled_quantity = float(order.quantity)
            order.trade_id = trade.id
            session.add(order)

            paper_trade = PaperTradeModel(
                position_id=trade.id,
                order_id=order.id,
                symbol=order.symbol,
                side=order.side,
                entry=float(entry),
                quantity=float(order.quantity),
                status=OPEN,
            )
            session.add(paper_trade)
            session.commit()
            session.refresh(order)
            session.refresh(paper_trade)
            session.expunge(order)
            session.expunge(paper_trade)

            return (
                PaperOrder.from_model(order),
                PaperPosition.from_trade(trade),
                PaperTrade.from_model(paper_trade),
            )
        except ValueError:
            session.rollback()
            raise
        except Exception:
            session.rollback()
            self.logger.exception("Failed to fill paper order: %s", order_id)
            return None
        finally:
            session.close()

    def cancel_order(self, order_id: int, reason: Optional[str] = None) -> Optional[PaperOrder]:
        """Cancel a pending paper order. Idempotent for already-cancelled orders."""
        session = self.session_factory()
        try:
            order = session.query(PaperOrderModel).filter(PaperOrderModel.id == order_id).first()
            if order is None:
                self.logger.warning("Paper order not found for cancel: %s", order_id)
                return None

            should_cancel = validate_cancel_order(order.status)
            if not should_cancel:
                self.logger.info("Paper order %s already cancelled (idempotent)", order_id)
                return PaperOrder.from_model(order)

            order.status = CANCEL
            if reason:
                order.reason = reason
            session.add(order)
            session.commit()
            session.refresh(order)
            session.expunge(order)
            self.logger.info("Paper order %s cancelled: %s", order_id, reason or "")
            return PaperOrder.from_model(order)
        except ValueError:
            raise
        except Exception:
            session.rollback()
            self.logger.exception("Failed to cancel paper order: %s", order_id)
            return None
        finally:
            session.close()

    @staticmethod
    def _legacy_status(status: str) -> str:
        mapping = {TAKE_PROFIT: TP_HIT, STOP_LOSS: SL_HIT}
        return mapping.get(status, status)

    @staticmethod
    def _has_open_trade_for_position(session: Any, position_id: int) -> bool:
        return (
            session.query(PaperTradeModel)
            .filter(
                PaperTradeModel.position_id == position_id,
                PaperTradeModel.status == OPEN,
            )
            .first()
            is not None
        )

    def close_position(
        self,
        trade_id: int,
        exit_price: float,
        status: str = CLOSED,
        close_reason: Optional[str] = None,
    ) -> Optional[tuple[PaperPosition, Optional[PaperTrade]]]:
        """Close a position and finalize the associated paper trade.

        Idempotent for already-closed positions.
        """
        session = self.session_factory()
        try:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if trade is None:
                self.logger.warning("Paper position not found for close: %s", trade_id)
                return None

            current_domain_status = _domain_status(str(trade.status)) if trade.status else OPEN
            should_close = validate_close_trade(
                current_domain_status,
                status,
            )
            if not should_close:
                self.logger.info("Paper position %s already closed (idempotent)", trade_id)
                session.expunge(trade)
                return PaperPosition.from_trade(trade), None

            result = self._positions.close_trade(
                trade_id=trade_id,
                exit_price=exit_price,
                status=self._legacy_status(status),
                close_reason=close_reason,
            )
            if result is None:
                return None

            session.refresh(trade)
            session.expunge(trade)

            paper_trade = (
                session.query(PaperTradeModel)
                .filter(PaperTradeModel.position_id == trade_id)
                .filter(PaperTradeModel.status == OPEN)
                .first()
            )
            if paper_trade is not None:
                paper_trade.status = status
                paper_trade.exit_price = float(exit_price)
                paper_trade.pnl = float(result.realized_pnl or 0)
                paper_trade.close_reason = close_reason or status
                paper_trade.closed_at = datetime.now(timezone.utc)
                session.add(paper_trade)
                session.commit()
                session.refresh(paper_trade)
                session.expunge(paper_trade)
                return (
                    PaperPosition.from_trade(trade),
                    PaperTrade.from_model(paper_trade),
                )

            return PaperPosition.from_trade(trade), None
        except ValueError:
            raise
        except Exception:
            session.rollback()
            self.logger.exception("Failed to finalize paper trade for position %s", trade_id)
            return None
        finally:
            session.close()

    def execute_signal(
        self,
        trade_id: int,
        entry: float,
        quantity: float,
    ) -> Optional[tuple[PaperOrder, PaperPosition, PaperTrade]]:
        """Execute a signal: create filled order + trade journal in one step.

        This is the primary integration point between the execution pipeline
        and the paper trading domain.  It creates a FILLED PaperOrder and an
        OPEN PaperTrade journal entry for an already-persisted position
        (Trade).

        Idempotent — returns the existing records if already executed for
        this position.
        """
        session = self.session_factory()
        try:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if trade is None:
                self.logger.warning("Trade not found for signal execution: %s", trade_id)
                return None

            existing_order = (
                session.query(PaperOrderModel)
                .filter(PaperOrderModel.trade_id == trade_id)
                .first()
            )
            if existing_order is not None:
                self.logger.info(
                    "Signal already executed for position %s (idempotent)", trade_id,
                )
                session.expunge(existing_order)
                existing_paper_trade = (
                    session.query(PaperTradeModel)
                    .filter(PaperTradeModel.position_id == trade_id)
                    .first()
                )
                if existing_paper_trade is not None:
                    session.expunge(existing_paper_trade)
                return (
                    PaperOrder.from_model(existing_order),
                    PaperPosition.from_trade(trade),
                    PaperTrade.from_model(existing_paper_trade) if existing_paper_trade else None,
                )

            order = PaperOrderModel(
                symbol=trade.symbol,
                side=trade.side,
                order_type="MARKET",
                quantity=float(quantity),
                price=float(entry),
                filled_price=float(entry),
                filled_quantity=float(quantity),
                status=FILLED,
                trade_id=trade.id,
            )
            session.add(order)
            session.flush()

            paper_trade = PaperTradeModel(
                position_id=trade.id,
                order_id=order.id,
                symbol=trade.symbol,
                side=trade.side,
                entry=float(entry),
                quantity=float(quantity),
                status=OPEN,
            )
            session.add(paper_trade)
            session.commit()
            session.refresh(order)
            session.refresh(paper_trade)
            session.expunge(order)
            session.expunge(paper_trade)
            trade_id_val = trade.id
            order_id_val = order.id
            paper_trade_id_val = paper_trade.id
            session.expunge(trade)

            self.logger.info(
                "Signal executed: position=%s order=%s trade=%s",
                trade_id_val, order_id_val, paper_trade_id_val,
            )

            return (
                PaperOrder.from_model(order),
                PaperPosition.from_trade(trade),
                PaperTrade.from_model(paper_trade),
            )
        except Exception:
            session.rollback()
            self.logger.exception("Failed to execute signal for trade %s", trade_id)
            return None
        finally:
            session.close()

    def get_open_positions(self) -> list[PaperPosition]:
        trades = self._positions.get_open_trades()
        return [PaperPosition.from_trade(t) for t in trades]

    def get_orders(
        self,
        status: Optional[str] = None,
    ) -> list[PaperOrder]:
        session = self.session_factory()
        try:
            query = session.query(PaperOrderModel)
            if status is not None:
                query = query.filter(PaperOrderModel.status == status)
            orders = query.all()
            for o in orders:
                session.expunge(o)
            return [PaperOrder.from_model(o) for o in orders]
        except Exception:
            self.logger.exception("Failed to load paper orders")
            return []
        finally:
            session.close()

    def get_trades(
        self,
        position_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> list[PaperTrade]:
        session = self.session_factory()
        try:
            query = session.query(PaperTradeModel)
            if position_id is not None:
                query = query.filter(PaperTradeModel.position_id == position_id)
            if status is not None:
                query = query.filter(PaperTradeModel.status == status)
            trades = query.all()
            for t in trades:
                session.expunge(t)
            return [PaperTrade.from_model(t) for t in trades]
        except Exception:
            self.logger.exception("Failed to load paper trades")
            return []
        finally:
            session.close()

    def monitor_positions(self) -> list[TradeMonitorResult]:
        return self._positions.monitor_open_trades()
