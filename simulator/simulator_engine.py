from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from simulator.models import (
    AIDecisionMode,
    EliteScore,
    MarketRegime,
    SimSpeed,
    SimStatus,
    SimulatedCandle,
    SimulatedDecision,
    SimulatedTrade,
    SimulatorConfig,
    SimulatorState,
    TimelineEvent,
)
from simulator.replay_engine import MarketReplayEngine
from simulator.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

SPEED_MULTIPLIERS: dict[SimSpeed, float] = {
    SimSpeed.SPEED_1X: 1.0,
    SimSpeed.SPEED_2X: 2.0,
    SimSpeed.SPEED_5X: 5.0,
    SimSpeed.SPEED_10X: 10.0,
    SimSpeed.SPEED_100X: 100.0,
    SimSpeed.UNLIMITED: 0.0,
}


class SimulatorEngine:
    def __init__(
        self,
        replay_engine: MarketReplayEngine | None = None,
        report_generator: ReportGenerator | None = None,
        council_engine: Any | None = None,
        evidence_engine: Any | None = None,
        paper_executor: Any | None = None,
        explain_engine: Any | None = None,
        position_sizer: Any | None = None,
        market_service: Any | None = None,
    ) -> None:
        self._replay = replay_engine or MarketReplayEngine()
        self._reports = report_generator or ReportGenerator()
        self._council = council_engine
        self._evidence = evidence_engine
        self._executor = paper_executor
        self._explain = explain_engine
        self._sizer = position_sizer
        self._market = market_service

        self._state: SimulatorState | None = None
        self._task: asyncio.Task | None = None
        self._paused = asyncio.Event()
        self._paused.set()
        self._stopped = asyncio.Event()
        self._stopped.set()
        self._state_listeners: list[Callable[[SimulatorState], None]] = []
        self._candle_listeners: list[Callable[[SimulatedCandle], None]] = []
        self._decision_listeners: list[Callable[[SimulatedDecision], None]] = []
        self._trade_listeners: list[Callable[[SimulatedTrade], None]] = []
        self._timeline_listeners: list[Callable[[TimelineEvent], None]] = []

    @property
    def state(self) -> SimulatorState | None:
        return self._state

    @property
    def running(self) -> bool:
        return self._state is not None and self._state.status == SimStatus.RUNNING

    def on_state(self, listener: Callable[[SimulatorState], None]) -> None:
        self._state_listeners.append(listener)

    def on_candle(self, listener: Callable[[SimulatedCandle], None]) -> None:
        self._candle_listeners.append(listener)

    def on_decision(self, listener: Callable[[SimulatedDecision], None]) -> None:
        self._decision_listeners.append(listener)

    def on_trade(self, listener: Callable[[SimulatedTrade], None]) -> None:
        self._trade_listeners.append(listener)

    def on_timeline(self, listener: Callable[[TimelineEvent], None]) -> None:
        self._timeline_listeners.append(listener)

    async def start(self, config: SimulatorConfig, name: str = "") -> str:
        if self._state and self._state.status == SimStatus.RUNNING:
            return self._state.session_id

        sid = uuid.uuid4().hex[:12]
        self._state = SimulatorState(
            session_id=sid,
            config=config,
            portfolio_value=config.initial_capital,
            cash=config.initial_capital,
        )

        candles_loaded = self._replay.load(
            symbol=config.symbol,
            timeframe=config.timeframe,
            start_date=config.start_date,
            end_date=config.end_date,
        )
        self._state.total_candles = candles_loaded
        self._status_change(SimStatus.RUNNING)
        self._paused.set()
        self._stopped.clear()
        self._emit_state()

        self._add_timeline("SIMULATION_START", f"Simulation started: {config.symbol} {config.timeframe}")

        self._task = asyncio.create_task(self._run_loop())
        return sid

    def pause(self) -> None:
        if self._state and self._state.status == SimStatus.RUNNING:
            self._paused.clear()
            self._status_change(SimStatus.PAUSED)
            self._add_timeline("SIMULATION_PAUSE", "Simulation paused")
            self._emit_state()

    def resume(self) -> None:
        if self._state and self._state.status == SimStatus.PAUSED:
            self._paused.set()
            self._status_change(SimStatus.RUNNING)
            self._add_timeline("SIMULATION_RESUME", "Simulation resumed")
            self._emit_state()

    def stop(self) -> SimulatorState | None:
        if self._state is None:
            return None
        self._stopped.set()
        self._paused.set()
        if self._task and not self._task.done():
            self._task.cancel()
        self._status_change(SimStatus.STOPPED)
        self._add_timeline("SIMULATION_STOP", "Simulation stopped")
        self._emit_state()
        return self._state

    def reset(self) -> None:
        self.stop()
        self._replay.reset()
        self._state = None
        self._task = None

    def step_candle(self) -> SimulatedCandle | None:
        if self._state is None or self._state.status != SimStatus.PAUSED:
            return None
        candle = self._replay.step()
        if candle:
            self._process_candle(candle)
            self._emit_state()
        return candle

    def seek_to(self, timestamp: int) -> bool:
        if self._state is None:
            return False
        candle = self._replay.seek_to_timestamp(timestamp)
        if candle:
            self._state.current_timestamp = candle.timestamp
            self._state.current_price = candle.close
            self._emit_state()
            return True
        return False

    def execute_manual_trade(
        self,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        quantity: float,
        leverage: float = 1.0,
        trailing_stop: float | None = None,
    ) -> SimulatedTrade | None:
        if self._state is None:
            return None
        trade = self._create_trade(side, entry_price, stop_loss, take_profit, quantity, leverage, trailing_stop, manual=True)
        if trade:
            self._state.trades.append(trade)
            self._state.open_positions += 1
            self._add_timeline("TRADE_MANUAL_OPEN", f"Manual {side} {trade.symbol} @ ${entry_price}", severity="trade")
            self._emit_state()
        return trade

    def close_trade(self, trade_id: str, exit_price: float | None = None) -> bool:
        if self._state is None:
            return False
        for t in self._state.trades:
            if t.id == trade_id and t.status == "OPEN":
                price = exit_price or self._state.current_price or t.entry_price
                self._close_trade(t, price, "MANUAL_CLOSE")
                self._add_timeline("TRADE_CLOSED", f"Closed {t.side} {t.symbol} @ ${price}", severity="trade")
                self._emit_state()
                return True
        return False

    def close_all_trades(self, exit_price: float | None = None) -> int:
        closed = 0
        for t in list(self._state.trades if self._state else []):
            if t.status == "OPEN":
                self.close_trade(t.id, exit_price)
                closed += 1
        return closed

    def get_report(self) -> Any:
        if self._state is None:
            return None
        return self._reports.generate(self._state)

    def get_report_json(self) -> str:
        report = self.get_report()
        return self._reports.export_json(report) if report else "{}"

    def get_report_pdf(self) -> bytes:
        report = self.get_report()
        return self._reports.export_pdf(report) if report else b""

    def export_session(self) -> dict[str, Any]:
        if self._state is None:
            return {}
        return self._state.to_dict()

    async def _run_loop(self) -> None:
        state = self._state
        if state is None:
            return
        config = state.config
        speed = SPEED_MULTIPLIERS.get(config.speed, 1.0)
        founder_metrics: dict[str, Any] = {
            "ai_latency_ms": [], "decision_latency_ms": [], "evidence_latency_ms": [],
        }

        while self._replay.index < self._replay.total:
            if self._stopped.is_set():
                break
            await self._paused.wait()

            candle_start = time.monotonic()
            candle = self._replay.step()
            if candle is None:
                break

            self._process_candle(candle)

            loop_duration = time.monotonic() - candle_start
            state.elapsed_seconds += loop_duration

            if config.founder_mode:
                founder_metrics["ai_latency_ms"].append(0)
                founder_metrics["decision_latency_ms"].append(0)
                founder_metrics["evidence_latency_ms"].append(0)
                state.founder_metrics = {
                    k: round(sum(v[-100:]) / len(v[-100:]), 2) if v else 0
                    for k, v in founder_metrics.items()
                }

            self._emit_state()

            if speed > 0:
                base_interval = self._get_interval(config.timeframe)
                sleep_time = base_interval / speed
                if sleep_time > 0.005:
                    await asyncio.sleep(sleep_time)

        if not self._stopped.is_set():
            self._status_change(SimStatus.COMPLETED)
            self._add_timeline("SIMULATION_COMPLETE", "Simulation completed")
            logger.info("Simulation %s completed (%s candles)", state.session_id, state.total_candles)
            self._emit_state()

    def _process_candle(self, candle: SimulatedCandle) -> None:
        state = self._state
        if state is None:
            return

        state.current_timestamp = candle.timestamp
        state.current_price = candle.close
        state.current_candle_index = self._replay.index

        regime = self._replay._detect_regime(candle)
        if regime != state.regime:
            old = state.regime
            state.regime = regime
            self._add_timeline("REGIME_CHANGE", f"Regime: {old.value} -> {regime.value}", data={"regime": regime.value})

        for listener in self._candle_listeners:
            listener(candle)

        if state.config.ai_mode != AIDecisionMode.MANUAL:
            decision = self._run_ai_decision(candle)
            if decision:
                state.decisions.append(decision)
                for listener in self._decision_listeners:
                    listener(decision)

                if state.config.ai_mode == AIDecisionMode.FULL_AI and decision.decision in ("BUY", "SELL"):
                    side = "LONG" if decision.decision == "BUY" else "SHORT"
                    self._execute_ai_trade(side, candle, decision)

        if state.open_positions > 0:
            self._monitor_open_trades(candle)

        # Unrealized mark-to-market value per open position: cash already
        # reflects a -quantity*entry_price debit at open (both sides), so the
        # position's current contribution to equity is that cost basis plus
        # unrealized PnL. For LONG this simplifies to quantity*close (the old
        # formula), but for SHORT unrealized PnL moves the opposite direction
        # -- using quantity*close for SHORT too silently inverts the sign.
        equity_value = state.cash + sum(
            (
                t.quantity * candle.close
                if t.side == "LONG"
                else t.quantity * (2 * t.entry_price - candle.close)
            )
            for t in state.trades
            if t.status == "OPEN"
        )
        state.portfolio_value = equity_value
        state.equity_curve.append({
            "timestamp": candle.timestamp,
            "value": round(equity_value, 2),
            "price": candle.close,
        })

    def _run_ai_decision(self, candle: SimulatedCandle) -> SimulatedDecision | None:
        state = self._state
        if state is None:
            return None
        try:
            decision_id = uuid.uuid4().hex[:12]
            council_report = None
            evidence_report = None
            explanation = None
            agent_reports: list[dict[str, Any]] = []
            conflicts: list[str] = []

            if self._council is not None:
                signal_mock = self._make_signal_mock(candle)
                council_result = self._council.evaluate(signal=signal_mock)
                council_report = council_result.to_dict() if hasattr(council_result, "to_dict") else {}
                agent_reports = council_report.get("agent_reports", [])
                if council_result:
                    conf = council_result.consensus_score
                    direction = council_result.consensus_direction
                else:
                    conf, direction = 0.5, "NEUTRAL"

                if hasattr(council_result, "sources_disagreeing") and council_result.sources_disagreeing > 2:
                    conflicts.append("High disagreement among council agents")
            else:
                conf = 0.5
                direction = "NEUTRAL"

            if self._evidence is not None:
                evidence_result = self._evidence.build(
                    council_result=council_report,
                    symbol=state.config.symbol,
                    recommendation=direction,
                )
                evidence_report = evidence_result.to_dict() if hasattr(evidence_result, "to_dict") else {}
                evidence_strength = evidence_report.get("evidence_strength", 0.5) if evidence_report else 0.5
            else:
                evidence_strength = conf

            if self._explain is not None:
                inp = self._make_explain_input(candle, conf, direction)
                explain_result = self._explain.explain(inp)
                explanation = explain_result.to_dict() if hasattr(explain_result, "to_dict") else {}

            risk_score_val = 1.0 - conf if direction in ("BEARISH",) else conf

            decision_signal = "HOLD"
            if direction == "BULLISH" and conf > 0.55:
                decision_signal = "BUY"
            elif direction == "BEARISH" and conf > 0.55:
                decision_signal = "SELL"

            sim_decision = SimulatedDecision(
                id=decision_id,
                symbol=state.config.symbol,
                side=direction,
                timestamp=candle.timestamp,
                price=candle.close,
                decision=decision_signal,
                confidence=round(conf * 100, 1),
                evidence_strength=round(evidence_strength * 100, 1),
                risk_score=round(risk_score_val * 100, 1),
                council_report=council_report,
                evidence_report=evidence_report,
                explanation=explanation,
                agent_reports=agent_reports,
                conflicts=conflicts,
            )

            self._add_timeline(
                "AI_DECISION",
                f"AI {decision_signal} | {direction} | {conf:.0%} confidence",
                data={"decision": decision_signal, "confidence": conf, "direction": direction},
                severity="decision",
            )

            return sim_decision
        except Exception as e:
            logger.warning("AI decision failed at candle %s: %s", self._replay.index, e)
            return None

    def _execute_ai_trade(self, side: str, candle: SimulatedCandle, decision: SimulatedDecision) -> None:
        state = self._state
        if state is None:
            return
        for t in state.trades:
            if t.status == "OPEN" and t.side == side:
                return

        entry = candle.close
        atr_val = self._estimate_atr() or entry * 0.02
        stop_loss = entry - atr_val * 1.5 if side == "LONG" else entry + atr_val * 1.5
        take_profit = entry + atr_val * 3 if side == "LONG" else entry - atr_val * 3

        risk_pct = state.config.risk_per_trade
        risk_amount = state.portfolio_value * risk_pct
        risk_per_unit = abs(entry - stop_loss)
        quantity = (risk_amount / risk_per_unit) if risk_per_unit > 0 else 0

        if quantity <= 0:
            return
        cost = quantity * entry
        if cost > state.cash:
            quantity = state.cash / entry
        if quantity <= 0:
            return

        trade = self._create_trade(
            side=side,
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
            leverage=state.config.leverage,
            manual=False,
            decision_id=decision.id,
            entry_decision=decision.to_dict(),
        )
        if trade:
            state.trades.append(trade)
            state.open_positions += 1
            state.cash -= quantity * entry
            self._add_timeline(
                "TRADE_AI_OPEN",
                f"AI {side} {state.config.symbol} @ ${entry:.2f} | qty={quantity:.4f}",
                data={"trade_id": trade.id, "side": side, "entry": entry, "quantity": quantity},
                severity="trade",
            )
            for listener in self._trade_listeners:
                listener(trade)

    def _monitor_open_trades(self, candle: SimulatedCandle) -> None:
        state = self._state
        if state is None:
            return
        for trade in list(state.trades):
            if trade.status != "OPEN":
                continue
            close_reason = None
            exit_price = None

            if trade.stop_loss > 0:
                if trade.side == "LONG" and candle.low <= trade.stop_loss:
                    close_reason = "STOP_LOSS"
                    exit_price = trade.stop_loss
                elif trade.side == "SHORT" and candle.high >= trade.stop_loss:
                    close_reason = "STOP_LOSS"
                    exit_price = trade.stop_loss

            if close_reason is None and trade.take_profit > 0:
                if trade.side == "LONG" and candle.high >= trade.take_profit:
                    close_reason = "TAKE_PROFIT"
                    exit_price = trade.take_profit
                elif trade.side == "SHORT" and candle.low <= trade.take_profit:
                    close_reason = "TAKE_PROFIT"
                    exit_price = trade.take_profit

            if close_reason:
                self._close_trade(trade, exit_price or candle.close, close_reason)
                self._add_timeline(
                    "TRADE_CLOSED",
                    f"{close_reason}: {trade.side} {trade.symbol} @ ${exit_price or candle.close:.2f} | PnL=${trade.pnl:.2f}",
                    data={"trade_id": trade.id, "reason": close_reason, "pnl": trade.pnl},
                    severity="trade",
                )
                for listener in self._trade_listeners:
                    listener(trade)

    def _create_trade(
        self,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        quantity: float,
        leverage: float = 1.0,
        trailing_stop: float | None = None,
        manual: bool = False,
        decision_id: str | None = None,
        entry_decision: dict[str, Any] | None = None,
    ) -> SimulatedTrade | None:
        if self._state is None:
            return None
        slippage = entry_price * (self._state.config.slippage_bps / 10000.0)
        fill_price = entry_price + slippage if side == "LONG" else entry_price - slippage
        notional = quantity * fill_price
        fee = notional * self._state.config.fee_rate
        trade = SimulatedTrade(
            id=uuid.uuid4().hex[:12],
            symbol=self._state.config.symbol,
            side=side,
            entry_price=round(fill_price, 2),
            entry_time=self._state.current_timestamp or 0,
            quantity=round(quantity, 6),
            leverage=leverage,
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            trailing_stop=round(trailing_stop, 2) if trailing_stop else None,
            fees=round(fee, 2),
            slippage=round(slippage, 2),
            decision_id=decision_id,
            entry_decision=entry_decision,
            elite_score=entry_decision.get("confidence", 50) if entry_decision else None,
        )
        return trade

    def _close_trade(self, trade: SimulatedTrade, exit_price: float, reason: str) -> None:
        side_mult = 1 if trade.side == "LONG" else -1
        gross_pnl = (exit_price - trade.entry_price) * trade.quantity * side_mult
        total_fees_entry = trade.fees
        total_fees_exit = exit_price * trade.quantity * self._state.config.fee_rate if self._state else 0
        net_pnl = gross_pnl - total_fees_entry - total_fees_exit

        trade.exit_price = round(exit_price, 2)
        trade.exit_time = self._state.current_timestamp if self._state else 0
        trade.pnl = round(net_pnl, 2)
        trade.pnl_percent = round((exit_price / trade.entry_price - 1) * side_mult * 100, 2)
        trade.fees = round(total_fees_entry + total_fees_exit, 2)
        trade.close_reason = reason
        trade.status = "CLOSED"

        if self._state:
            self._state.open_positions = max(0, self._state.open_positions - 1)
            self._state.total_pnl += net_pnl
            if net_pnl > 0:
                self._state.win_count += 1
            else:
                self._state.loss_count += 1
            self._state.cash += trade.quantity * exit_price - total_fees_exit if trade.side == "LONG" else trade.quantity * exit_price - total_fees_exit

    def _status_change(self, status: SimStatus) -> None:
        if self._state:
            self._state.status = status

    def _add_timeline(
        self, event_type: str, title: str, severity: str = "info", data: dict[str, Any] | None = None
    ) -> None:
        if self._state is None:
            return
        event = TimelineEvent(
            id=uuid.uuid4().hex[:12],
            timestamp=self._state.current_timestamp or 0,
            event_type=event_type,
            symbol=self._state.config.symbol,
            title=title,
            description=title,
            severity=severity,
            data=data,
        )
        self._state.timeline.append(event)
        for listener in self._timeline_listeners:
            listener(event)

    def _emit_state(self) -> None:
        if self._state is None:
            return
        for listener in self._state_listeners:
            listener(self._state)

    def _make_signal_mock(self, candle: SimulatedCandle) -> Any:
        from unittest.mock import MagicMock
        signal = MagicMock()
        signal.id = 0
        signal.symbol = self._state.config.symbol if self._state else "BTC"
        signal.side = "LONG"
        signal.timeframe = self._state.config.timeframe if self._state else "1h"
        signal.price = candle.close
        signal.score = 0.5
        signal.confidence = 0.5
        signal.trend_score = 0.5
        signal.volume_score = 0.5
        signal.risk_score = 0.5
        signal.btc_health = 0.5
        signal.funding_score = 0.5
        signal.oi_score = 0.5
        signal.cvd_score = 0.5
        return signal

    def _make_explain_input(self, candle: SimulatedCandle, confidence: float, direction: str) -> Any:
        try:
            from explain.core import ExplainInput
            return ExplainInput(
                symbol=self._state.config.symbol if self._state else "BTC",
                side="LONG" if direction == "BULLISH" else "SHORT",
                technical_score=confidence,
                whale_score=0.5,
                news_score=0.5,
                risk_score=0.5,
                trend_score=0.5,
                portfolio_total_equity=self._state.portfolio_value if self._state else 10000,
                portfolio_unrealized_pnl=0,
                portfolio_realized_pnl=self._state.total_pnl if self._state else 0,
                portfolio_exposure=0,
                portfolio_initial_capital=self._state.config.initial_capital if self._state else 10000,
                performance_sharpe=0,
                performance_sortino=0,
                performance_calmar=0,
                performance_profit_factor=0,
                performance_win_rate=0,
                performance_total_pnl=self._state.total_pnl if self._state else 0,
                performance_max_drawdown=0,
            )
        except ImportError:
            return None

    def _estimate_atr(self) -> float | None:
        candles = self._replay.get_range(max(0, self._replay.index - 14), 14)
        if len(candles) < 2:
            return None
        trs = []
        for i in range(1, len(candles)):
            tr = max(
                candles[i].high - candles[i].low,
                abs(candles[i].high - candles[i - 1].close),
                abs(candles[i].low - candles[i - 1].close),
            )
            trs.append(tr)
        return sum(trs) / len(trs)

    def _get_interval(self, timeframe: str) -> float:
        intervals = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}
        return float(intervals.get(timeframe, 3600))
