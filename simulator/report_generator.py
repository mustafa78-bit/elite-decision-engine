from __future__ import annotations

import json
import logging
import statistics
from datetime import datetime, timezone
from typing import Any, Optional

from simulator.models import (
    EliteScore,
    MarketRegime,
    MissionReport,
    SimStatus,
    SimulatedTrade,
    SimulatorConfig,
    SimulatorState,
    TrainingScore,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    def generate(self, state: SimulatorState) -> MissionReport:
        trades = state.trades
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl < 0]
        total_wl = len(wins) + len(losses)

        win_rate = len(wins) / total_wl * 100 if total_wl > 0 else 0.0
        total_pnl = sum(t.pnl for t in trades)
        total_fees = sum(t.fees for t in trades)
        total_slippage = sum(t.slippage for t in trades)

        avg_win = statistics.mean([t.pnl for t in wins]) if wins else 0.0
        avg_loss = statistics.mean([abs(t.pnl) for t in losses]) if losses else 0.0
        largest_win = max([t.pnl for t in wins]) if wins else 0.0
        largest_loss = max([abs(t.pnl) for t in losses]) if losses else 0.0

        # profit_factor is gross_profit / gross_loss (sums), not avg_win/avg_loss
        # -- the average-based ratio only equals the real profit factor when
        # win_count == loss_count, and is wildly wrong otherwise.
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)

        equity = [e.get("value", state.config.initial_capital) for e in state.equity_curve]
        max_drawdown, max_drawdown_pct = self._compute_max_drawdown(equity)

        returns = [equity[i] / equity[i - 1] - 1 for i in range(1, len(equity)) if equity[i - 1] > 0]
        sharpe = self._compute_sharpe(returns) if returns else 0.0

        avg_holding = 0.0
        holding_times = []
        for t in trades:
            if t.entry_time and t.exit_time:
                holding_times.append((t.exit_time - t.entry_time) / 1000.0)
        if holding_times:
            avg_holding = statistics.mean(holding_times)

        regime_changes = self._detect_regime_changes(state)

        elite_scores = []
        for t in trades:
            if t.elite_score is not None:
                elite_scores.append(EliteScore(
                    overall=t.elite_score,
                    confidence=t.entry_decision.get("confidence", 0) if t.entry_decision else 0,
                    evidence_strength=t.entry_decision.get("evidence_strength", 0) if t.entry_decision else 0,
                    risk=t.entry_decision.get("risk_score", 0) if t.entry_decision else 0,
                    execution=0.0,
                    reward=max(0, t.pnl) / (abs(t.pnl) + 1),
                ))

        training_score = self._compute_training_score(state)
        mistakes = self._find_mistakes(state)
        lessons = self._generate_lessons(mistakes, training_score)
        recommendations = self._generate_recommendations(training_score, state)

        final_value = state.portfolio_value
        initial = state.config.initial_capital
        return_pct = (final_value - initial) / initial * 100 if initial > 0 else 0.0

        return MissionReport(
            session_id=state.session_id,
            config=state.config,
            duration_seconds=state.elapsed_seconds,
            total_candles=state.total_candles,
            total_decisions=len(state.decisions),
            total_trades=len(trades),
            wins=len(wins),
            losses=len(losses),
            win_rate=round(win_rate, 2),
            total_pnl=round(total_pnl, 2),
            total_fees=round(total_fees, 2),
            total_slippage=round(total_slippage, 2),
            max_drawdown=round(max_drawdown, 2),
            max_drawdown_pct=round(max_drawdown_pct, 2),
            sharpe_ratio=round(sharpe, 4),
            profit_factor=round(profit_factor, 4),
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            largest_win=round(largest_win, 2),
            largest_loss=round(largest_loss, 2),
            avg_holding_time=round(avg_holding, 2),
            final_portfolio_value=round(final_value, 2),
            return_pct=round(return_pct, 2),
            regime_changes=regime_changes,
            elite_scores=elite_scores,
            training_score=training_score,
            trades=trades,
            decisions=state.decisions,
            timeline=state.timeline,
            equity_curve=state.equity_curve,
            mistakes=mistakes,
            lessons=lessons,
            ai_recommendations=recommendations,
        )

    def export_json(self, report: MissionReport) -> str:
        return json.dumps(report.to_dict(), indent=2, default=str)

    def export_pdf(self, report: MissionReport) -> bytes:
        try:
            from io import BytesIO

            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=letter)
            styles = getSampleStyleSheet()
            elements: list[Any] = []
            elements.append(Paragraph(f"Mission Report: {report.session_id}", styles["Title"]))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Symbol: {report.config.symbol} | Timeframe: {report.config.timeframe}", styles["Normal"]))
            elements.append(Paragraph(f"Duration: {report.duration_seconds}s | Candles: {report.total_candles}", styles["Normal"]))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Total Trades: {report.total_trades} | Win Rate: {report.win_rate}%", styles["Normal"]))
            elements.append(Paragraph(f"Total PnL: ${report.total_pnl} | Return: {report.return_pct}%", styles["Normal"]))
            elements.append(Paragraph(f"Sharpe: {report.sharpe_ratio} | Max Drawdown: {report.max_drawdown_pct}%", styles["Normal"]))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Training Scores", styles["Heading2"]))
            ts = report.training_score
            elements.append(Paragraph(f"Patience: {ts.patience:.1f} | Risk: {ts.risk:.1f} | Timing: {ts.timing:.1f}", styles["Normal"]))
            elements.append(Paragraph(f"Entry Quality: {ts.entry_quality:.1f} | Exit Quality: {ts.exit_quality:.1f}", styles["Normal"]))
            elements.append(Paragraph(f"Psychology: {ts.psychology:.1f} | Discipline: {ts.discipline:.1f}", styles["Normal"]))
            doc.build(elements)
            return buf.getvalue()
        except ImportError:
            logger.warning("reportlab not available for PDF export")
            return b""

    def _compute_max_drawdown(self, equity: list[float]) -> tuple[float, float]:
        if not equity:
            return 0.0, 0.0
        peak = equity[0]
        max_dd = 0.0
        max_dd_pct = 0.0
        for v in equity:
            if v > peak:
                peak = v
            dd = peak - v
            dd_pct = dd / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct
        return max_dd, max_dd_pct

    def _compute_sharpe(self, returns: list[float]) -> float:
        if len(returns) < 2:
            return 0.0
        mean = statistics.mean(returns)
        std = statistics.stdev(returns)
        if std == 0:
            return 0.0
        return mean / std * (252 ** 0.5)

    def _detect_regime_changes(self, state: SimulatorState) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        current = None
        for event in state.timeline:
            if event.event_type == "REGIME_CHANGE" and event.data:
                regime = event.data.get("regime", "")
                if regime != current:
                    current = regime
                    changes.append({
                        "timestamp": event.timestamp,
                        "regime": regime,
                        "title": event.title,
                    })
        return changes

    def _compute_training_score(self, state: SimulatorState) -> TrainingScore:
        trades = state.trades
        score = TrainingScore()
        if not trades:
            return score

        score.patience = self._score_patience(trades)
        score.risk = self._score_risk(trades, state.config)
        score.timing = self._score_timing(trades)
        score.entry_quality = self._score_entry_quality(trades)
        score.exit_quality = self._score_exit_quality(trades)
        score.psychology = self._score_psychology(trades)
        score.discipline = self._score_discipline(trades)

        return score

    def _score_patience(self, trades: list[SimulatedTrade]) -> float:
        if len(trades) < 3:
            return 50.0
        holding_times = []
        for t in trades:
            if t.entry_time and t.exit_time:
                holding_times.append((t.exit_time - t.entry_time) / 1000.0 / 3600.0)
        if not holding_times:
            return 50.0
        avg_hours = statistics.mean(holding_times)
        if avg_hours < 0.5:
            return 20.0
        if avg_hours < 2:
            return 40.0
        if avg_hours < 8:
            return 60.0
        if avg_hours < 48:
            return 80.0
        return 90.0

    def _score_risk(self, trades: list[SimulatedTrade], config: SimulatorConfig) -> float:
        if not trades:
            return 50.0
        with_sl = sum(1 for t in trades if t.stop_loss > 0)
        ratio = with_sl / len(trades)
        if ratio >= 0.9:
            return 90.0
        if ratio >= 0.7:
            return 70.0
        if ratio >= 0.5:
            return 50.0
        return 30.0

    def _score_timing(self, trades: list[SimulatedTrade]) -> float:
        if not trades:
            return 50.0
        wins = [t for t in trades if t.pnl > 0]
        if not wins:
            return 30.0
        win_ratio = len(wins) / len(trades)
        return 30.0 + win_ratio * 70.0

    def _score_entry_quality(self, trades: list[SimulatedTrade]) -> float:
        if not trades:
            return 50.0
        entries_before_move = 0
        for t in trades:
            # entry_decision["confidence"] is stored on a 0-100 scale (see
            # simulator_engine.py's _run_ai_decision(): round(conf * 100, 1)),
            # not 0-1 -- compare against a matching threshold.
            if t.entry_decision and t.entry_decision.get("confidence", 0) > 60:
                entries_before_move += 1
        return min(100.0, entries_before_move / len(trades) * 100)

    def _score_exit_quality(self, trades: list[SimulatedTrade]) -> float:
        if not trades:
            return 50.0
        good_exits = 0
        for t in trades:
            if t.close_reason in ("TAKE_PROFIT", "TP_HIT", "TRAILING_STOP"):
                good_exits += 1
            elif t.close_reason == "STOP_LOSS" and abs(t.pnl_percent) < 2:
                good_exits += 1
        return min(100.0, good_exits / len(trades) * 100)

    def _score_psychology(self, trades: list[SimulatedTrade]) -> float:
        if len(trades) < 3:
            return 50.0
        reversals = 0
        for t in trades:
            if t.close_reason == "REVERSAL":
                reversals += 1
        panic_sells = sum(1 for t in trades if t.close_reason == "STOP_LOSS" and abs(t.pnl_percent) > 5)
        score = 100.0 - (reversals * 10) - (panic_sells * 5)
        return max(0.0, min(100.0, score))

    def _score_discipline(self, trades: list[SimulatedTrade]) -> float:
        if not trades:
            return 50.0
        with_tp_sl = sum(1 for t in trades if t.stop_loss > 0 and t.take_profit > 0)
        ratio = with_tp_sl / len(trades)
        return ratio * 100.0

    def _find_mistakes(self, state: SimulatorState) -> list[str]:
        mistakes: list[str] = []
        trades = state.trades
        if not trades:
            mistakes.append("No trades executed during simulation")
            return mistakes
        for t in trades:
            if t.close_reason == "STOP_LOSS" and abs(t.pnl_percent) > 5:
                mistakes.append(f"Wide stop loss on {t.symbol} {t.side} lost {abs(t.pnl_percent):.1f}%")
            if t.close_reason == "SL_HIT" and abs(t.pnl_percent) > 3:
                mistakes.append(f"Stop loss hit with large loss: {t.symbol} -{abs(t.pnl_percent):.1f}%")
        if state.win_count + state.loss_count > 5:
            win_rate = state.win_count / (state.win_count + state.loss_count) * 100
            if win_rate < 30:
                mistakes.append(f"Low win rate ({win_rate:.0f}%) — review entry criteria")
        return mistakes or ["No significant mistakes detected"]

    def _generate_lessons(self, mistakes: list[str], score: TrainingScore) -> list[str]:
        lessons: list[str] = []
        if score.patience < 50:
            lessons.append("Work on patience — hold trades longer to capture full moves")
        if score.risk < 50:
            lessons.append("Always use stop losses — protect capital")
        if score.timing < 50:
            lessons.append("Improve entry timing — wait for confirmation")
        if score.exit_quality < 50:
            lessons.append("Set take profit targets and trail stops")
        if score.psychology < 50:
            lessons.append("Manage emotions — avoid panic selling and reversals")
        if score.discipline < 50:
            lessons.append("Follow your trading plan consistently")
        for m in mistakes:
            if "no trades" in m.lower():
                lessons.append("Take more trades — learn from experience")
                break
        return lessons or ["Keep practicing — maintain good habits"]

    def _generate_recommendations(self, score: TrainingScore, state: SimulatorState) -> list[str]:
        recs: list[str] = []
        if score.patience < 60:
            recs.append("Use higher timeframe confirmation before entering")
        if score.risk < 60:
            recs.append("Set stop loss at 1-2x ATR for each trade")
        if score.timing < 60:
            recs.append("Wait for candle close confirmation before entry")
        if score.entry_quality < 60:
            recs.append("Use AI Council evaluation to filter low-conviction setups")
        if score.exit_quality < 60:
            recs.append("Implement trailing stops to lock profits")
        if score.psychology < 60:
            recs.append("Use automated execution to remove emotional decisions")
        if score.discipline < 60:
            recs.append("Create a trading checklist and follow it for every trade")
        return recs or ["Current strategy shows good discipline"]
