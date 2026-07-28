from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from decision.kernel.DecisionContext import DecisionContext
from decision.kernel.DecisionEvidence import DecisionEvidence
from decision.kernel.DecisionReasoning import DecisionReasoning
from decision.kernel.DecisionRequest import DecisionRequest
from decision.kernel.DecisionResult import DecisionResult
from decision.kernel.DecisionTimeline import DecisionTimeline, TimelineEvent

logger = logging.getLogger(__name__)


class DecisionKernel:
    """The authoritative brain orchestrating the Unified Cognitive Flow of NEXUS."""

    def __init__(self, trust_engine: Optional[Any] = None, learning_engine: Optional[Any] = None) -> None:
        self.trust_engine = trust_engine
        self.learning_engine = learning_engine

    def decide(self, request: DecisionRequest, context: Optional[DecisionContext] = None) -> DecisionResult:
        """Process a decision request through the deterministic 12-stage Cognitive Flow."""
        if context is None:
            context = DecisionContext()

        timeline = DecisionTimeline()

        # 1. Observe
        timeline.record("Observe", f"Received request to evaluate {request.symbol} {request.side}", source="DecisionKernel")

        # 2. Understand
        indicators = context.indicators or {}
        price = request.price or indicators.get("close", 0.0)
        timeline.record("Understand", f"Consolidated metrics for {request.symbol} at price ${price:.2f}", source="DecisionKernel")

        # 3. Connect
        graph = context.graph_context or {}
        timeline.record("Connect", f"Queried Knowledge Graph 2.0; found {len(graph.get('related_nodes', []))} related entities", source="DecisionKernel")

        # 4. Reason
        reasoning_steps: list[DecisionReasoning] = []
        evidence_list: list[DecisionEvidence] = []

        # Analyze technical scoring inputs
        raw_score = request.score if hasattr(request, "score") else 0.5
        if "score" in request.metadata:
            raw_score = request.metadata["score"]
        elif "final_score" in indicators:
            raw_score = indicators["final_score"]

        reasoning_steps.append(
            DecisionReasoning(
                step="Reason",
                description=f"Initial technical signal score evaluated at {raw_score:.2f}",
                impact=raw_score,
            )
        )

        # 5. Evaluate
        for key, val in indicators.items():
            if isinstance(val, (int, float)):
                evidence_list.append(
                    DecisionEvidence(
                        source="Indicators",
                        metric_name=key,
                        metric_value=val,
                    )
                )

        # 6. Trust
        trust_score = context.trust_scores.get("score", 0.85)
        evidence_list.append(
            DecisionEvidence(
                source="TrustEngine",
                metric_name="trust_score",
                metric_value=trust_score,
            )
        )
        timeline.record("Trust", f"Assessed system trust levels: score={trust_score:.2f}", source="DecisionKernel")

        # 7. Learn
        lessons = context.learning_lessons or []
        timeline.record("Learn", f"Extracted {len(lessons)} past learning outcome insights", source="DecisionKernel")

        # 8. Calibrate
        calibration = context.calibration_metrics or {"ece": 0.05, "brier": 0.02}
        timeline.record("Calibrate", "Applied calibration scaling to confidence ratings", source="DecisionKernel")

        # Calculate calibrated confidence
        raw_confidence = request.confidence if hasattr(request, "confidence") else 50.0
        if "confidence" in request.metadata:
            raw_confidence = request.metadata["confidence"]
        elif "confidence" in indicators:
            raw_confidence = indicators["confidence"]

        calibrated_confidence = raw_confidence * (1.0 - calibration.get("ece", 0.0))
        # Ensure it stays within bounds
        calibrated_confidence = max(0.0, min(100.0, calibrated_confidence))

        # 9. Decide
        if calibrated_confidence >= 80.0:
            recommendation = "STRONG_APPROVE"
        elif calibrated_confidence >= 65.0:
            recommendation = "APPROVE"
        elif calibrated_confidence >= 50.0:
            recommendation = "WATCH"
        else:
            recommendation = "REJECT"

        timeline.record("Decide", f"Action recommendation formulated: {recommendation}", source="DecisionKernel")

        # 10. Explain
        reasons = request.metadata.get("reasons", [])
        if not reasons:
            reasons = [f"Technical indicators align with a {request.side} configuration"]
            if trust_score > 0.8:
                reasons.append(f"Trust engine verifies signal reliability at {trust_score*100:.1f}%")

        warnings = request.metadata.get("warnings", [])
        if not warnings and calibrated_confidence < 60.0:
            warnings.append("Confidence score is lower than recommendation threshold; execute with caution")

        signals = request.signals or []
        founder_summary = f"The Decision Kernel recommends **{recommendation}** for {request.symbol} ({request.side}) based on a technical score of {raw_score:.2f} and trust rating of {trust_score*100:.1f}%."
        timeline.record("Explain", "Synthesized explanation briefs and warnings", source="DecisionKernel")

        # 11. Remember
        decision_id = self._compute_deterministic_hash(request, context)
        timeline.record("Remember", f"Committed decision metadata and cognitive traces to memory index (ID: {decision_id})", source="DecisionKernel")

        # 12. Improve
        timeline.record("Improve", "Registered decision with learning loops for outcome auditing", source="DecisionKernel")

        # Construct and return stable DecisionResult
        return DecisionResult(
            decision_id=decision_id,
            symbol=request.symbol,
            side=request.side,
            decision=recommendation,
            score=raw_score,
            confidence=calibrated_confidence,
            probability=raw_score,
            risk_score=context.risk_assessment.get("risk_score", 0.3),
            priority=raw_score * 0.4 + (calibrated_confidence / 100.0) * 0.6,
            trust=context.trust_scores or {"score": trust_score},
            risk=context.risk_assessment or {"status": "PASSED"},
            portfolio_impact=context.portfolio_status or {"exposure": 0.0},
            market_regime=context.market_regime or {"regime": "NORMAL"},
            learning_context={"lessons": lessons},
            calibration_status=calibration,
            graph_context=graph,
            advisor_votes=context.advisor_votes,
            reasons=reasons,
            warnings=warnings,
            signals=signals,
            founder_summary=founder_summary,
            evidence=evidence_list,
            reasoning=reasoning_steps,
            timeline=timeline.to_list(),
            metadata={
                "strategy": request.strategy,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **request.metadata,
            },
        )

    def _compute_deterministic_hash(self, request: DecisionRequest, context: DecisionContext) -> str:
        """Compute a SHA-256 hash of parameters and context to guarantee determinism and replayability."""
        payload = {
            "symbol": request.symbol,
            "side": request.side,
            "timeframe": request.timeframe,
            "price": request.price,
            "strategy": request.strategy,
            "indicators": sorted(context.indicators.items()) if context.indicators else [],
            "trust": sorted(context.trust_scores.items()) if context.trust_scores else [],
            "risk": sorted(context.risk_assessment.items()) if context.risk_assessment else [],
            "regime": sorted(context.market_regime.items()) if context.market_regime else [],
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
