from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from config import SCORE_WEIGHTS
from dto.explanations import (
    ConfidenceBreakdownDTO,
    DecisionExplanationDTO,
    DecisionMetadataDTO,
    DecisionReasoningDTO,
    DecisionTimelineDTO,
    IntelligenceContributionDTO,
    MarketContributionDTO,
    MemoryContributionDTO,
    RiskContributionDTO,
    StrategyContributionDTO,
)

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExplanationService:
    """Explainable AI service providing human-readable decision justifications.

    Aggregates data from scoring, risk, intelligence, memory, and strategy
    engines into a structured, explainable decision report.
    """

    def __init__(
        self,
        scoring_engine: Optional[Any] = None,
        confidence_engine: Optional[Any] = None,
        intelligence_collector: Optional[Any] = None,
        trade_memory: Optional[Any] = None,
        strategy_scorer: Optional[Any] = None,
        regime_ai: Optional[Any] = None,
    ):
        self._scoring = scoring_engine
        self._confidence = confidence_engine
        self._intelligence = intelligence_collector
        self._memory = trade_memory
        self._strategy_scorer = strategy_scorer
        self._regime_ai = regime_ai

    def explain_signal(self, signal: Any, scores: Optional[dict[str, Any]] = None) -> DecisionExplanationDTO:
        start = time.perf_counter()
        sid = getattr(signal, "id", 0) if not isinstance(signal, dict) else signal.get("id", 0)
        symbol = getattr(signal, "symbol", "?") if not isinstance(signal, dict) else signal.get("symbol", "?")

        timeline = DecisionTimelineDTO(signal_id=sid)
        timeline.add_event("explain_start", f"Explaining signal {symbol}")

        if not scores and signal is not None:
            # Check if signal has any scoring attributes/keys
            has_scoring = False
            for attr in ("score", "confidence", "trend_score", "volume_score", "btc_health", "btc_score", "risk_score"):
                if isinstance(signal, dict):
                    if attr in signal:
                        has_scoring = True
                        break
                else:
                    if hasattr(signal, attr):
                        has_scoring = True
                        break

            if has_scoring:
                def get_val(obj, attr, default=0.0):
                    if isinstance(obj, dict):
                        return obj.get(attr, default)
                    return getattr(obj, attr, default)

                entry = get_val(signal, "price", 0.0) or get_val(signal, "entry", 0.0)
                final_score = get_val(signal, "score", 0.0) or get_val(signal, "final_score", 0.0)
                confidence = get_val(signal, "confidence", 0.0) or (final_score * 100.0 if final_score else 0.0)

                trend_score = get_val(signal, "trend_score", 0.0)
                volume_score = get_val(signal, "volume_score", 0.0)
                btc_score = get_val(signal, "btc_health", 0.0) or get_val(signal, "btc_score", 0.0)
                risk_score = get_val(signal, "risk_score", 0.0)

                mtf_score = get_val(signal, "mtf_score", None)
                if mtf_score is None:
                    numerator = final_score - (trend_score * 0.30 + volume_score * 0.20 + btc_score * 0.20 + risk_score * 0.10)
                    mtf_score = max(0.0, min(1.0, numerator / 0.20)) if final_score > 0 else 0.0

                scores = {
                    "entry": entry,
                    "ema20": get_val(signal, "ema20", 0.0),
                    "ema50": get_val(signal, "ema50", 0.0),
                    "ema200": get_val(signal, "ema200", 0.0),
                    "rsi": get_val(signal, "rsi", 50.0),
                    "atr": get_val(signal, "atr", 0.0),
                    "trend_score": trend_score,
                    "volume_score": volume_score,
                    "btc_score": btc_score,
                    "mtf_score": mtf_score,
                    "risk_score": risk_score,
                    "final_score": final_score,
                    "confidence": confidence,
                    "volatility_score": get_val(signal, "volatility_score", 0.0),
                    "contributions": {
                        "trend": round(trend_score * SCORE_WEIGHTS.get("trend", 0.30), 4),
                        "volume": round(volume_score * SCORE_WEIGHTS.get("volume", 0.20), 4),
                        "btc": round(btc_score * SCORE_WEIGHTS.get("btc", 0.20), 4),
                        "mtf": round(mtf_score * SCORE_WEIGHTS.get("mtf", 0.20), 4),
                        "risk": round(risk_score * SCORE_WEIGHTS.get("risk", 0.10), 4),
                    }
                }

        reasoning = self._build_reasoning(signal, scores, timeline)
        reasoning.human_readable = self._build_human_readable(reasoning)

        timeline.add_event("explain_complete", "Explanation generated")
        elapsed = (time.perf_counter() - start) * 1000

        metadata = self._build_metadata(signal, elapsed)
        timeline.total_duration_ms = round(elapsed, 2)

        return DecisionExplanationDTO(
            reasoning=reasoning,
            timeline=timeline,
            metadata=metadata,
        )

    def _build_reasoning(
        self,
        signal: Any,
        scores: Optional[dict[str, Any]],
        timeline: DecisionTimelineDTO,
    ) -> DecisionReasoningDTO:
        sid = getattr(signal, "id", 0)
        symbol = getattr(signal, "symbol", "?")
        side = getattr(signal, "side", "?")
        timeframe = getattr(signal, "timeframe", "?")
        entry = 0.0
        status = getattr(signal, "status", "?")
        decision = "?"

        if scores:
            entry = scores.get("entry", 0.0)
            final = scores.get("final_score", 0)
            confidence = scores.get("confidence") or final * 100 if scores else 0

            timeline.add_event("confidence_breakdown", "Computing confidence breakdown")
            cb = self._build_confidence_breakdown(scores, confidence)
            decision = cb.decision

            timeline.add_event("risk_contribution", "Computing risk contribution")
            rc = self._build_risk_contribution(scores)

            timeline.add_event("intelligence_contribution", "Computing intelligence contribution")
            ic = self._build_intelligence_contribution(symbol)

            timeline.add_event("market_contribution", "Computing market contribution")
            mc = self._build_market_contribution(symbol, scores)

            timeline.add_event("strategy_contribution", "Computing strategy contribution")
            sc = self._build_strategy_contribution(symbol, side)

            timeline.add_event("memory_contribution", "Computing memory contribution")
            memc = self._build_memory_contribution(symbol, side)
        else:
            cb = ConfidenceBreakdownDTO()
            rc = RiskContributionDTO()
            ic = IntelligenceContributionDTO()
            mc = MarketContributionDTO(symbol=symbol)
            sc = StrategyContributionDTO()
            memc = MemoryContributionDTO()

        return DecisionReasoningDTO(
            signal_id=sid,
            symbol=symbol,
            side=side,
            timeframe=timeframe,
            entry_price=entry,
            status=status,
            decision=decision,
            confidence_breakdown=cb,
            risk_contribution=rc,
            intelligence_contribution=ic,
            market_contribution=mc,
            strategy_contribution=sc,
            memory_contribution=memc,
        )

    def _build_confidence_breakdown(
        self, scores: dict[str, Any], confidence: float
    ) -> ConfidenceBreakdownDTO:
        ts = scores.get("trend_score", 0)
        vs = scores.get("volume_score", 0)
        bs = scores.get("btc_score", 0)
        ms = scores.get("mtf_score", 0)
        rs = scores.get("risk_score", 0)
        final = scores.get("final_score", 0)

        contributions = scores.get("contributions", {})
        dec = "REJECT"
        if confidence >= 90:
            dec = "STRONG_APPROVE"
        elif confidence >= 80:
            dec = "APPROVE"
        elif confidence >= 70:
            dec = "WATCH"

        return ConfidenceBreakdownDTO(
            trend_score=ts,
            volume_score=vs,
            btc_score=bs,
            mtf_score=ms,
            risk_score=rs,
            trend_contribution=contributions.get("trend", ts * SCORE_WEIGHTS.get("trend", 0.30)),
            volume_contribution=contributions.get("volume", vs * SCORE_WEIGHTS.get("volume", 0.20)),
            btc_contribution=contributions.get("btc", bs * SCORE_WEIGHTS.get("btc", 0.20)),
            mtf_contribution=contributions.get("mtf", ms * SCORE_WEIGHTS.get("mtf", 0.20)),
            risk_contribution=contributions.get("risk", rs * SCORE_WEIGHTS.get("risk", 0.10)),
            final_score=final,
            confidence=confidence,
            decision=dec,
        )

    def _build_risk_contribution(self, scores: dict[str, Any]) -> RiskContributionDTO:
        atr = scores.get("atr", 0)
        vol_score = scores.get("volatility_score", 0)
        risk_score = scores.get("risk_score", 1.0)

        atr_impact = "low"
        if atr > 2500:
            atr_impact = "extreme"
        elif atr > 1500:
            atr_impact = "high"
        elif atr > 300:
            atr_impact = "moderate"

        vol_class = "UNKNOWN"
        if vol_score > 0.05:
            vol_class = "HIGH"
        elif vol_score > 0.02:
            vol_class = "NORMAL"
        else:
            vol_class = "LOW"

        return RiskContributionDTO(
            atr=atr,
            volatility_score=vol_score,
            risk_score=risk_score,
            penalties={
                "volatility": round(vol_score * 0.60, 4),
            },
            atr_impact=atr_impact,
            volatility_class=vol_class,
        )

    def _build_intelligence_contribution(self, symbol: str) -> IntelligenceContributionDTO:
        if self._intelligence is None:
            return IntelligenceContributionDTO()

        try:
            bundle = self._intelligence.collect(symbol)
            return IntelligenceContributionDTO(
                funding_risk=bundle.funding_risk,
                oi_trend=bundle.oi_trend,
                confidence=bundle.confidence,
                feature_count=bundle.feature_count,
                available_features=bundle.availability.active_features if bundle.availability else [],
            )
        except Exception as e:
            logger.warning("Intelligence contribution failed for %s: %s", symbol, e)
            return IntelligenceContributionDTO()

    def _build_market_contribution(
        self, symbol: str, scores: dict[str, Any]
    ) -> MarketContributionDTO:
        regime = "UNKNOWN"
        vol_class = "UNKNOWN"
        if self._regime_ai and scores:
            try:
                regime_result = self._regime_ai.detect(scores)
                regime = regime_result.get("regime", "UNKNOWN")
                vol_class = regime_result.get("volatility_class", "UNKNOWN")
            except Exception:
                pass

        return MarketContributionDTO(
            symbol=symbol,
            price=scores.get("entry", 0),
            ema20=scores.get("ema20", 0),
            ema50=scores.get("ema50", 0),
            ema200=scores.get("ema200", 0),
            rsi=scores.get("rsi", 50),
            atr=scores.get("atr", 0),
            volume_24h=scores.get("volume_score", 0),
            volatility_class=vol_class,
            regime=regime,
        )

    def _build_strategy_contribution(
        self, symbol: str, side: str
    ) -> StrategyContributionDTO:
        if self._strategy_scorer is None:
            return StrategyContributionDTO()

        try:
            return StrategyContributionDTO(
                strategy_name="CompositeStrategy",
                confidence=0.5,
                score=0.5,
                signals_count=0,
                win_rate=0.0,
            )
        except Exception as e:
            logger.warning("Strategy contribution failed: %s", e)
            return StrategyContributionDTO()

    def _build_memory_contribution(
        self, symbol: str, side: str
    ) -> MemoryContributionDTO:
        if self._memory is None:
            return MemoryContributionDTO()

        try:
            stats = self._memory.stats()
            return MemoryContributionDTO(
                total_entries=stats.get("total_entries", 0),
                wins=stats.get("wins", 0),
                losses=stats.get("losses", 0),
                win_rate_pct=stats.get("win_rate_pct", 0),
                total_pnl=stats.get("total_pnl", 0),
                similar_trades_count=0,
                similar_trades_win_rate=0.0,
            )
        except Exception as e:
            logger.warning("Memory contribution failed: %s", e)
            return MemoryContributionDTO()

    def _build_human_readable(self, reasoning: DecisionReasoningDTO) -> str:
        parts = []
        cb = reasoning.confidence_breakdown

        if reasoning.decision:
            parts.append(f"Decision: {reasoning.decision}")
        if reasoning.symbol and reasoning.side:
            parts.append(f"Signal: {reasoning.symbol} {reasoning.side} ({reasoning.timeframe})")

        if cb and cb.final_score > 0:
            parts.append(f"Final score: {cb.final_score:.3f}, Confidence: {cb.confidence:.1f}%")
            top = max(
                ("Trend", cb.trend_contribution),
                ("Volume", cb.volume_contribution),
                ("BTC Health", cb.btc_contribution),
                ("Multi-Timeframe", cb.mtf_contribution),
                ("Risk", cb.risk_contribution),
                key=lambda x: x[1],
            )
            parts.append(f"Biggest contributor: {top[0]} ({top[1]:.4f})")

        if reasoning.risk_contribution:
            rc = reasoning.risk_contribution
            parts.append(f"Risk: score={rc.risk_score}, ATR impact={rc.atr_impact}")

        if reasoning.market_contribution:
            mc = reasoning.market_contribution
            parts.append(f"Market: RSI={mc.rsi:.1f}, Regime={mc.regime}, Vol={mc.volatility_class}")

        if reasoning.intelligence_contribution:
            ic = reasoning.intelligence_contribution
            if ic.feature_count > 0:
                parts.append(f"Intelligence: {ic.feature_count} features, confidence={ic.confidence:.2f}")

        if reasoning.memory_contribution:
            memc = reasoning.memory_contribution
            if memc.total_entries > 0:
                parts.append(f"Memory: {memc.total_entries} entries, win rate={memc.win_rate_pct:.1f}%")

        return " | ".join(parts)

    def _build_metadata(
        self, signal: Any, processing_time_ms: float
    ) -> DecisionMetadataDTO:
        return DecisionMetadataDTO(
            signal_id=getattr(signal, "id", 0),
            model_version="1.0",
            engine_version="1.0",
            data_freshness_seconds=3600,
            total_sources_evaluated=6,
            sources_available=6,
            sources_unavailable=0,
            processing_time_ms=round(processing_time_ms, 2),
            explanation_version="2.0",
        )
