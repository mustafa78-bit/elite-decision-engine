import time
from typing import Any, Dict, List, Optional

from database import get_session, Signal
from config import CHECK_INTERVAL
from core.intelligence import IntelligenceBundle
from decision.models import DecisionContext, DecisionExplanation, DecisionFactor, DecisionSnapshot


class DecisionEngine:

    def __init__(self, intelligence=None):
        print("Decision Engine initialized")
        self.intelligence = intelligence or IntelligenceBundle()
        self.decision_history: List[DecisionSnapshot] = []
        self._max_history = 1000

    def get_open_signals(self):
        session = get_session()

        try:
            return (
                session.query(Signal)
                .filter(Signal.status == "OPEN")
                .all()
            )
        finally:
            session.close()

    def process_signal(self, signal):
        print("=" * 50)
        print(f"Coin      : {signal.symbol}")
        print(f"Side      : {signal.side}")
        print(f"Timeframe : {signal.timeframe}")

        intelligence_result = self.intelligence.evaluate()

        btc_ok = intelligence_result.get("btc", {}).get("ok", True)
        whale_ok = intelligence_result.get("whale", {}).get("ok", True)
        liquidity_ok = intelligence_result.get("liquidity", {}).get("ok", True)
        orderflow_ok = intelligence_result.get("orderflow", {}).get("ok", True)
        ms_ok = intelligence_result.get("market_structure", {}).get("ok", True)
        news_ok = intelligence_result.get("news", {}).get("ok", True)
        sentiment_ok = intelligence_result.get("sentiment", {}).get("ok", True)
        macro_ok = intelligence_result.get("macro", {}).get("ok", True)

        context = self._build_context(signal, intelligence_result)
        explanation = DecisionExplanation()

        if signal.side.upper() == "LONG":
            if not btc_ok:
                explanation.add_rejection_reason("BTC market not healthy")
                explanation.decision = "REJECTED"
                print("RED -> BTC market not healthy.")
                self._record_snapshot(signal, context, explanation, 0.0)
                print("=" * 50)
                return

        if not whale_ok:
            explanation.add_rejection_reason("Whale data unavailable or unhealthy")
            print("WARNING -> Whale data unavailable or unhealthy.")
        else:
            explanation.add_approval_reason("Whale data healthy")

        if not liquidity_ok:
            explanation.add_rejection_reason("Liquidity data unavailable or unhealthy")
            print("WARNING -> Liquidity data unavailable or unhealthy.")
        else:
            explanation.add_approval_reason("Liquidity data healthy")

        if not orderflow_ok:
            explanation.add_rejection_reason("Order flow data unavailable or unhealthy")
            print("WARNING -> Order flow data unavailable or unhealthy.")
        else:
            explanation.add_approval_reason("Order flow data healthy")

        if not ms_ok:
            explanation.add_rejection_reason("Market structure data unavailable or unhealthy")
            print("WARNING -> Market structure data unavailable or unhealthy.")
        else:
            explanation.add_approval_reason("Market structure data healthy")

        if not news_ok:
            explanation.add_rejection_reason("News data unavailable or unhealthy")
            print("WARNING -> News data unavailable or unhealthy.")
        else:
            explanation.add_approval_reason("News data healthy")

        if not sentiment_ok:
            explanation.add_rejection_reason("Sentiment data unavailable or unhealthy")
            print("WARNING -> Sentiment data unavailable or unhealthy.")
        else:
            explanation.add_approval_reason("Sentiment data healthy")

        if not macro_ok:
            explanation.add_rejection_reason("Macro data unavailable or unhealthy")
            print("WARNING -> Macro data unavailable or unhealthy.")
        else:
            explanation.add_approval_reason("Macro data healthy")

        explanation.decision = "APPROVED"
        explanation.add_approval_reason("All critical checks passed")
        print("APPROVED")
        print("=" * 50)

        self._record_snapshot(signal, context, explanation, 100.0)

    def _build_context(
        self, signal, intelligence_result: Dict[str, Any]
    ) -> DecisionContext:
        ctx = DecisionContext(
            signal_symbol=signal.symbol,
            signal_side=signal.side,
            signal_timeframe=signal.timeframe,
            signal_id=getattr(signal, "id", 0),
            base_score=getattr(signal, "score", 0.0),
            intelligence_data=intelligence_result,
        )
        for module_key in ("whale", "liquidity", "orderflow", "market_structure", "news", "sentiment", "macro"):
            module = intelligence_result.get(module_key, {})
            ok_val = 1.0 if module.get("ok", True) else 0.0
            ctx.add_factor(DecisionFactor(
                name=f"{module_key}_health",
                value=ok_val,
                weight=1.0,
                source=module_key,
                description=f"{module_key} module health status",
            ))
        return ctx

    def _record_snapshot(
        self,
        signal,
        context: DecisionContext,
        explanation: DecisionExplanation,
        score: float,
    ) -> None:
        snapshot = DecisionSnapshot(
            signal_id=getattr(signal, "id", 0),
            decision=explanation.decision,
            score=score,
            context=context,
            explanation=explanation,
            confidence=score,
        )
        self.decision_history.append(snapshot)
        if len(self.decision_history) > self._max_history:
            self.decision_history = self.decision_history[-self._max_history:]

    def get_decision_history(
        self, n: int = 10
    ) -> List[Dict[str, Any]]:
        recent = self.decision_history[-n:]
        return [s.to_dict() for s in recent]

    def run(self):
        while True:
            signals = self.get_open_signals()

            if len(signals) == 0:
                print("No pending signals.")
            else:
                print(f"{len(signals)} new signal(s) found.")

                for signal in signals:
                    self.process_signal(signal)

            time.sleep(CHECK_INTERVAL)
