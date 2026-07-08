from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from database import JournalEntry, get_session, update_signal_status
from exchange.base import ExchangeAdapter
from execution.pipeline import DecisionPipeline, TradingSignal
from orders.order_manager import OrderManager
from risk.execution_guard import ExecutionGuard

logger = logging.getLogger(__name__)


@dataclass
class ShadowResult:
    signal_id: int
    symbol: str
    side: str
    approved: bool
    guard_passed: bool
    order_placed: bool
    journal_id: Optional[int] = None
    reason: str = ""


class ShadowEngine:
    """Shadow trading engine running the full signal-to-journal flow in paper mode.

    Flow: Signal -> DecisionPipeline -> ExecutionGuard -> OrderManager -> JournalEntry
    """

    def __init__(
        self,
        pipeline: Optional[DecisionPipeline] = None,
        guard: Optional[ExecutionGuard] = None,
        order_manager: Optional[OrderManager] = None,
        exchange: Optional[ExchangeAdapter] = None,
    ) -> None:
        self.pipeline = pipeline or DecisionPipeline()
        self.guard = guard or ExecutionGuard()
        self.order_manager = order_manager or OrderManager()
        self.logger = logger

        if exchange is not None:
            self.guard.set_exchange(exchange)
            self.order_manager.set_exchange(exchange)

    def process(self, signal: TradingSignal) -> ShadowResult:
        """Process a single signal through the full shadow trading flow."""
        self.logger.info(
            "Shadow processing signal %s: %s %s",
            signal.id, signal.symbol, signal.side,
        )

        # 1. Decision pipeline
        candidate = self.pipeline.evaluate(signal)
        if candidate is None:
            update_signal_status(signal.id, "REJECTED")
            self._record_journal(signal=signal, result="REJECTED", reason="Pipeline rejected")
            return ShadowResult(
                signal_id=signal.id,
                symbol=signal.symbol,
                side=signal.side,
                approved=False,
                guard_passed=False,
                order_placed=False,
                reason="Pipeline rejected",
            )

        update_signal_status(signal.id, "APPROVED")
        self.logger.info("Signal %s approved by pipeline", signal.id)

        # 2. Execution guard
        guard_result = self.guard.can_execute(
            symbol=candidate.symbol,
            side=candidate.side,
            entry_price=float(candidate.entry or 0),
            quantity=1.0,
        )

        if not guard_result.allowed:
            update_signal_status(signal.id, "BLOCKED")
            self._record_journal(
                signal=signal,
                result="BLOCKED",
                reason=f"Guard blocked: {guard_result.reason}",
                score=candidate.scores.get("final_score", 0) if candidate.scores else 0,
                confidence=candidate.confidence,
                entry_price=float(candidate.entry or 0),
            )
            return ShadowResult(
                signal_id=signal.id,
                symbol=candidate.symbol,
                side=candidate.side,
                approved=True,
                guard_passed=False,
                order_placed=False,
                reason=f"Guard blocked: {guard_result.reason}",
            )

        self.logger.info("Signal %s passed execution guard", signal.id)

        # 3. Place shadow order
        try:
            entry_price = Decimal(str(candidate.entry or 0))
            order = self.order_manager.create_order(
                symbol=candidate.symbol,
                side="BUY" if candidate.side == "LONG" else "SELL",
                order_type="MARKET",
                quantity=Decimal("1"),
                price=entry_price,
            )
            update_signal_status(signal.id, "EXECUTED")
            self.logger.info("Shadow order placed for signal %s: %s", signal.id, order.id)

            journal_id = self._record_journal(
                signal=signal,
                result="EXECUTED",
                reason="Shadow trade executed",
                score=candidate.scores.get("final_score", 0) if candidate.scores else 0,
                confidence=candidate.confidence,
                entry_price=float(candidate.entry or 0),
                order_id=order.id,
            )

            return ShadowResult(
                signal_id=signal.id,
                symbol=candidate.symbol,
                side=candidate.side,
                approved=True,
                guard_passed=True,
                order_placed=True,
                journal_id=journal_id,
                reason="Shadow trade executed",
            )

        except Exception as e:
            update_signal_status(signal.id, "ORDER_FAILED")
            self.logger.error("Shadow order failed for signal %s: %s", signal.id, e)
            return ShadowResult(
                signal_id=signal.id,
                symbol=candidate.symbol,
                side=candidate.side,
                approved=True,
                guard_passed=True,
                order_placed=False,
                reason=f"Order failed: {e}",
            )

    def process_batch(self, signals: list[TradingSignal]) -> list[ShadowResult]:
        """Process a batch of signals through the shadow trading flow."""
        return [self.process(s) for s in signals]

    def _record_journal(
        self,
        signal: TradingSignal,
        result: str,
        reason: str,
        score: float = 0.0,
        confidence: float = 0.0,
        entry_price: Optional[float] = None,
        order_id: Optional[str] = None,
    ) -> Optional[int]:
        session = get_session()
        try:
            entry = JournalEntry(
                symbol=signal.symbol,
                side=signal.side,
                entry_price=entry_price or 0.0,
                score=score,
                confidence=confidence,
                entry_reason=reason,
                result=result,
                signal_id=signal.id,
            )
            session.add(entry)
            session.commit()
            return entry.id
        except Exception as e:
            session.rollback()
            logger.error("Failed to record journal entry: %s", e)
            return None
        finally:
            session.close()
