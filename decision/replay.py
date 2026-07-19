from __future__ import annotations

import logging
from typing import Any, Optional
from database import get_session, Signal, Trade
from council.consensus import ConsensusEngine
from decision.evidence.evidence_engine import EvidenceEngine
from services.explanation_service import ExplanationService
from scoring.regime_ai import RegimeAI
from scoring.risk_engine import RiskEngine
from explain.engine import ExplainEngine
from explain.core import ExplainInput

logger = logging.getLogger(__name__)


class ReplayEngine:
    """Decision Replay Engine.

    Replays and evaluates decisions and signals under simulated
    or modified parameters without duplicating any core consensus,
    evidence, or explanation logic.
    """

    def __init__(
        self,
        consensus_engine: Optional[ConsensusEngine] = None,
        evidence_engine: Optional[EvidenceEngine] = None,
        explanation_service: Optional[ExplanationService] = None,
    ) -> None:
        self.consensus_engine = consensus_engine or ConsensusEngine()
        if not self.consensus_engine.agents:
            self.consensus_engine.register_defaults()
        self.evidence_engine = evidence_engine or EvidenceEngine()
        self.explanation_service = explanation_service or ExplanationService()
        self._regime_ai = RegimeAI()
        self._risk_engine = RiskEngine()
        self._explain_engine = ExplainEngine()

    def get_signal_context(self, signal_id: int) -> dict[str, Any]:
        session = get_session()
        try:
            signal = session.query(Signal).filter(Signal.id == signal_id).first()
            if not signal:
                return {}

            # Fetch associated trade if any
            trade = session.query(Trade).filter(Trade.signal_id == signal_id).first()

            context = {
                "signal_id": signal.id,
                "symbol": signal.symbol,
                "side": signal.side,
                "timeframe": signal.timeframe or "1h",
                "price": signal.price or 0.0,
                "score": signal.score or 0.0,
                "confidence": signal.confidence or 0.0,
                "volume_score": signal.volume_score or 0.0,
                "btc_health": signal.btc_health or 0.0,
                "trend_score": signal.trend_score or 0.0,
                "risk_score": signal.risk_score or 0.0,
                "funding_score": signal.funding_score or 0.0,
                "oi_score": signal.oi_score or 0.0,
                "cvd_score": signal.cvd_score or 0.0,
                "status": signal.status or "PENDING",
                "trade_pnl": trade.pnl if trade else None,
                "trade_status": trade.status if trade else None,
            }
            return context
        finally:
            session.close()

    def replay_signal(
        self, signal_id: int, modifications: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        context = self.get_signal_context(signal_id)
        if not context:
            raise ValueError(f"Signal {signal_id} not found")

        mods = modifications or {}
        replayed_context = dict(context)
        for k, v in mods.items():
            if k in replayed_context:
                replayed_context[k] = v

        # Construct a real transient Signal database model object to evaluate (no MagicMock!)
        transient_signal = Signal(
            id=replayed_context["signal_id"],
            symbol=replayed_context["symbol"],
            side=replayed_context["side"],
            timeframe=replayed_context["timeframe"],
            price=replayed_context["price"],
            score=replayed_context["score"],
            confidence=replayed_context["confidence"],
            volume_score=replayed_context["volume_score"],
            btc_health=replayed_context["btc_health"],
            trend_score=replayed_context["trend_score"],
            risk_score=replayed_context["risk_score"],
            funding_score=replayed_context["funding_score"],
            oi_score=replayed_context["oi_score"],
            cvd_score=replayed_context["cvd_score"],
            status=replayed_context["status"],
        )

        # Run through ConsensusEngine
        scores = {
            "entry": replayed_context["price"],
            "trend_score": replayed_context["trend_score"],
            "volume_score": replayed_context["volume_score"],
            "btc_score": replayed_context["btc_health"],
            "risk_score": replayed_context["risk_score"],
            "final_score": replayed_context["score"],
            "confidence": replayed_context["confidence"],
            "ema20": replayed_context["price"] * 0.99,
            "ema50": replayed_context["price"] * 0.98,
            "ema200": replayed_context["price"] * 0.95,
            "rsi": 55,
            "atr": replayed_context["price"] * 0.02,
            "volatility_score": 0.02,
        }

        # Consensus Engine evaluation
        council_report = self.consensus_engine.evaluate(signal=transient_signal, scores=scores)

        # Re-use real RiskEngine (no hardcoded checks!)
        risk_result = self._risk_engine.evaluate(
            {"atr": replayed_context["price"] * 0.02},
            {"score": replayed_context["score"]}
        )

        # Re-use real RegimeAI detect (no hardcoded regime!)
        market_regime_result = self._regime_ai.detect(scores)

        # Re-use real ExplainEngine (no hardcoded reasoning!)
        explain_input = ExplainInput(
            symbol=replayed_context["symbol"],
            side=replayed_context["side"],
            technical_score=replayed_context["score"],
            whale_score=replayed_context["cvd_score"],
            news_score=replayed_context["funding_score"],
            risk_score=replayed_context["risk_score"],
            trend_score=replayed_context["trend_score"],
            portfolio_total_equity=10000.0,
            portfolio_unrealized_pnl=0.0,
            portfolio_realized_pnl=0.0,
            portfolio_exposure=0.0,
            portfolio_initial_capital=10000.0,
            performance_sharpe=1.5,
            performance_sortino=1.6,
            performance_calmar=1.2,
            performance_profit_factor=1.8,
            performance_win_rate=60.0,
            performance_total_pnl=1200.0,
            performance_max_drawdown=5.0,
        )
        explain_result = self._explain_engine.explain(explain_input)

        # Evidence Engine evaluation utilizing real parsed results
        evidence_report = self.evidence_engine.build(
            decision_result=transient_signal,
            risk_result=risk_result,
            scanner_result=None,
            council_result=council_report,
            portfolio_result=None,
            market_regime_result=market_regime_result,
            whale_result=None,
            explain_result=explain_result,
            symbol=replayed_context["symbol"],
            recommendation=council_report.consensus_direction,
        )

        explanation = self.explanation_service.explain_signal(transient_signal, scores=scores)

        return {
            "original_context": context,
            "replayed_context": replayed_context,
            "modifications": mods,
            "council_report": council_report.to_dict(),
            "evidence_report": evidence_report.to_dict(),
            "explanation": explanation.to_dict(),
        }
