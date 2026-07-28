from __future__ import annotations

import logging
from typing import Any, Optional

from core.ledger import LedgerService
from database import update_signal_status
from execution.pipeline import DecisionPipeline, TradeCandidate, TradingSignal
from execution.trade_engine import TradeEngine
from position_sizing import PositionSizingEngine
from risk_manager import RiskManager

logger = logging.getLogger(__name__)


class DecisionKernel:
    """Central decision and orchestration layer of the NEXUS platform.

    Every signal evaluation, risk check, trade execution, and trade closure
    must pass through this orchestration layer, with every step recorded
    chronologically in the append-only Decision/Event Ledger.
    """

    def __init__(
        self,
        ledger_service: Optional[LedgerService] = None,
        pipeline: Optional[DecisionPipeline] = None,
        risk_manager: Optional[RiskManager] = None,
        position_sizer: Optional[PositionSizingEngine] = None,
        trade_engine: Optional[TradeEngine] = None,
        trade_journal: Optional[Any] = None,
    ) -> None:
        self.ledger = ledger_service or LedgerService()
        self.pipeline = pipeline or DecisionPipeline()
        self.risk_manager = risk_manager or RiskManager()
        self.position_sizer = position_sizer or PositionSizingEngine()
        self.trade_engine = trade_engine or TradeEngine()
        self.trade_journal = trade_journal

    def evaluate_and_execute_signal(self, signal: TradingSignal) -> Optional[Any]:
        """Orchestrate a signal through the decision, risk, sizing, and execution phases."""
        if signal is None:
            logger.warning("DecisionKernel received None signal")
            return None

        symbol = getattr(signal, "symbol", "UNKNOWN")
        side = getattr(signal, "side", "UNKNOWN")
        timeframe = getattr(signal, "timeframe", "UNKNOWN")

        # 1. Record Signal Created
        self.ledger.append_event(
            event_type="Signal Created",
            symbol=symbol,
            signal_id=signal.id,
            description=f"Trading signal created for {symbol} ({side}) timeframe={timeframe}",
            details={
                "id": signal.id,
                "symbol": symbol,
                "side": side,
                "timeframe": timeframe,
                "price": getattr(signal, "price", None),
            },
        )

        # 2. Evaluate with Pipeline (Decision Generated)
        candidate = self.pipeline.evaluate(signal)
        if candidate is None:
            logger.info("Signal rejected by decision pipeline: %s %s", symbol, side)
            update_signal_status(signal.id, "REJECTED")
            self.ledger.append_event(
                event_type="Decision Generated",
                symbol=symbol,
                signal_id=signal.id,
                description=f"Signal {symbol} {side} rejected by pipeline evaluation",
                details={
                    "decision": "REJECT",
                    "confidence": 0.0,
                    "reasoning": "Pipeline evaluation returned None (insufficient score or filter mismatch)",
                },
            )
            return None

        # Record Decision Generated
        self.ledger.append_event(
            event_type="Decision Generated",
            symbol=symbol,
            signal_id=signal.id,
            description=f"Pipeline generated decision: {candidate.decision} with confidence {candidate.confidence}%",
            details={
                "decision": candidate.decision,
                "confidence": candidate.confidence,
                "scores": dict(candidate.scores) if candidate.scores else {},
                "reasoning": f"Score threshold and filters met. Confidence calculated mathematically.",
                "market_context": {
                    "btc_health": getattr(signal, "btc_health", None),
                    "market_health": getattr(signal, "market_health", None),
                    "regime_context": candidate.regime_context,
                    "memory_context": candidate.memory_context,
                },
            },
        )

        # 3. Evaluate Risk (Risk Evaluation)
        risk_decision = self.risk_manager.evaluate_trade(candidate)
        if not risk_decision.allowed:
            logger.warning(
                "Trade rejected by risk manager: %s %s - reason=%s",
                symbol, side, risk_decision.reason,
            )
            update_signal_status(signal.id, "REJECTED")
            self.ledger.append_event(
                event_type="Risk Evaluation",
                symbol=symbol,
                signal_id=signal.id,
                description=f"Trade rejected by Risk Manager: {risk_decision.reason}",
                details={
                    "allowed": False,
                    "rejection_code": risk_decision.rejection_code,
                    "reason": risk_decision.reason,
                },
            )
            return None

        self.ledger.append_event(
            event_type="Risk Evaluation",
            symbol=symbol,
            signal_id=signal.id,
            description=f"Trade approved by Risk Manager",
            details={
                "allowed": True,
                "exposure_checked": True,
            },
        )

        # 4. Sizing and Execution (Trade Executed)
        position_size = self.position_sizer.calculate(candidate)
        trade = self._create_trade_record(candidate, position_size)

        if trade is not None:
            # Handle journaling
            if self.trade_journal is not None:
                journal_result = self.trade_journal.execute_signal(
                    trade_id=trade.id,
                    entry=float(candidate.entry) if candidate.entry else 0.0,
                    quantity=float(position_size.quantity),
                )
                if journal_result is not None:
                    paper_order, paper_position, paper_trade = journal_result
                    logger.info("Trade journal linked for trade_id=%s", trade.id)
                else:
                    logger.warning("Trade journal returned None for trade %s", trade.id)

            self.ledger.append_event(
                event_type="Trade Executed",
                symbol=symbol,
                signal_id=signal.id,
                trade_id=trade.id,
                description=f"Trade executed for {symbol} ({side}) at entry={trade.entry}",
                details={
                    "trade_id": trade.id,
                    "entry_price": trade.entry,
                    "stop_loss": trade.stop,
                    "take_profit_1": trade.tp1,
                    "take_profit_2": trade.tp2,
                    "quantity": float(position_size.quantity),
                    "notional_value": float(position_size.notional_value),
                    "risk_amount": float(position_size.risk_amount),
                    "exchange_order_id": trade.exchange_order_id,
                },
            )

            # 5. Feedback / Learning Hook
            self.ledger.append_event(
                event_type="Feedback Stored",
                symbol=symbol,
                signal_id=signal.id,
                trade_id=trade.id,
                description=f"Initial tracking feedback stored for learning loop on {symbol}",
                details={
                    "stage": "EXECUTION",
                    "decision_confidence": candidate.confidence,
                    "reasoning": f"ATR-based SL set at {trade.stop}. Target TP1 set at {trade.tp1}.",
                    "market_context": {
                        "btc_health": getattr(signal, "btc_health", None),
                        "market_health": getattr(signal, "market_health", None),
                        "regime_context": candidate.regime_context,
                        "memory_context": candidate.memory_context,
                    },
                },
            )
        else:
            logger.warning("TradeEngine failed to create trade for %s", symbol)
            update_signal_status(signal.id, "OPEN")

        return trade

    def register_trade_closed(
        self,
        trade_id: int,
        exit_price: float,
        reason: str,
        pnl: float,
        symbol: Optional[str] = None,
        signal_id: Optional[int] = None,
    ) -> None:
        """Register that a trade has closed, calculating outcome and recording to the Ledger."""
        # 1. Trade Closed
        self.ledger.append_event(
            event_type="Trade Closed",
            symbol=symbol,
            signal_id=signal_id,
            trade_id=trade_id,
            description=f"Trade {trade_id} closed on {symbol} due to {reason} at price {exit_price}",
            details={
                "trade_id": trade_id,
                "exit_price": exit_price,
                "close_reason": reason,
                "pnl": pnl,
            },
        )

        # 2. Outcome Calculated
        success = pnl > 0
        self.ledger.append_event(
            event_type="Outcome Calculated",
            symbol=symbol,
            signal_id=signal_id,
            trade_id=trade_id,
            description=f"Trade outcome computed: {'SUCCESS' if success else 'FAILURE'} with pnl={pnl}",
            details={
                "trade_id": trade_id,
                "pnl": pnl,
                "success": success,
                "result_class": "WIN" if success else "LOSS",
            },
        )

        # 3. Feedback/Learning Hook Stored
        self.ledger.append_event(
            event_type="Feedback Stored",
            symbol=symbol,
            signal_id=signal_id,
            trade_id=trade_id,
            description=f"Post-closure learning feedback stored for trade {trade_id}",
            details={
                "stage": "CLOSURE",
                "success": success,
                "pnl": pnl,
                "reason_for_success": reason if success else None,
                "reason_for_failure": reason if not success else None,
                "performance": {
                    "closed_at_price": exit_price,
                    "close_reason": reason,
                },
            },
        )

    def _create_trade_record(self, candidate: TradeCandidate, position_size: Any) -> Optional[Any]:
        entry = candidate.entry
        atr = candidate.scores.get("atr")

        if entry is None or atr is None:
            return None

        intelligence = {
            "confidence": candidate.confidence,
            "decision": candidate.decision,
            **candidate.scores,
        }
        if candidate.regime_context is not None:
            intelligence["regime_context"] = candidate.regime_context
        if candidate.memory_context is not None:
            intelligence["memory_context"] = candidate.memory_context

        return self.trade_engine.create_trade(
            signal=candidate.signal,
            entry=float(entry),
            atr=float(atr),
            intelligence=intelligence,
        )
