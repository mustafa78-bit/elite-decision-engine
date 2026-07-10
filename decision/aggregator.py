"""DecisionAggregator — aggregates signal, scanner, and intelligence into decisions."""

from __future__ import annotations

import logging
from typing import Any, Optional

from decision.confidence_v2 import ConfidenceEngineV2
from decision.explanation import ReasonBuilder, RiskExplanation, SignalExplanation
from decision.models import DecisionResult
from decision.timeline import DecisionTimeline
from market.models import Asset
from market.services import MarketDataService
from scanner.core import OpportunityScanner
from scanner.models import Opportunity

logger = logging.getLogger(__name__)


class DecisionAggregator:
    """Aggregate all intelligence into actionable decisions."""

    def __init__(
        self,
        scanner: Optional[OpportunityScanner] = None,
        market_service: Optional[MarketDataService] = None,
        confidence_engine: Optional[ConfidenceEngineV2] = None,
        timeline: Optional[DecisionTimeline] = None,
        reason_builder: Optional[ReasonBuilder] = None,
        risk_explanation: Optional[RiskExplanation] = None,
    ) -> None:
        self.scanner = scanner or OpportunityScanner()
        self.market_service = market_service or MarketDataService()
        self.confidence = confidence_engine or ConfidenceEngineV2()
        self.timeline = timeline or DecisionTimeline()
        self.reason_builder = reason_builder or ReasonBuilder()
        self.risk_explanation = risk_explanation or RiskExplanation()
        self.signal_explanation = SignalExplanation()

    def analyze(self, symbol: str, timeframe: str = "1h") -> Optional[DecisionResult]:
        asset = self.market_service.get_asset(symbol, timeframe)
        if asset.is_empty:
            return None

        self.timeline.record(symbol, "fetch", f"Fetched Asset data for {symbol}", source="MIP")

        scans = self.scanner.scan(symbols=[symbol], timeframe=timeframe)
        if not scans:
            return None

        opportunity = scans[0]

        self.timeline.record(symbol, "scan", f"Scanner found {opportunity.side} opportunity (score={opportunity.score:.3f})", source="Scanner")

        conf = self.confidence.evaluate_opportunity(opportunity, asset)
        opportunity.confidence = conf

        self.timeline.record(symbol, "confidence", f"Confidence scored at {conf:.1f}", source="ConfidenceEngineV2")

        reasons = self.reason_builder.build(opportunity, asset)
        warnings = self.reason_builder.build_warnings(opportunity)

        if conf >= 80:
            decision = "STRONG_APPROVE"
        elif conf >= 65:
            decision = "APPROVE"
        elif conf >= 50:
            decision = "WATCH"
        else:
            decision = "REJECT"

        self.timeline.record(symbol, "decision", f"Decision: {decision} (confidence={conf:.1f})", source="DecisionAggregator")

        signals = opportunity.signals + opportunity.probability_signals + opportunity.risk_signals

        result = DecisionResult(
            symbol=symbol,
            side=opportunity.side,
            decision=decision,
            score=opportunity.score,
            confidence=conf,
            probability=opportunity.probability_score,
            risk_score=opportunity.risk_score,
            reasons=reasons,
            warnings=warnings,
            signals=list(set(signals)),
            timeline=[],
            intelligence_summary=self._build_intel_summary(asset),
            feature_summary=dict(asset.features),
        )

        result = self.timeline.build_timeline(result)
        return result

    def analyze_multiple(
        self, symbols: list[str], timeframe: str = "1h", top_n: int = 5
    ) -> list[DecisionResult]:
        results: list[DecisionResult] = []
        for symbol in symbols:
            result = self.analyze(symbol, timeframe)
            if result is not None:
                results.append(result)

        results.sort(key=lambda r: r.confidence, reverse=True)
        return results[:top_n]

    def _build_intel_summary(self, asset: Asset) -> dict[str, Any]:
        bundle = asset.intelligence
        if bundle is None:
            return {}
        return {
            "fear_greed": bundle.fear_greed.get("label", "UNKNOWN") if bundle.fear_greed else "UNKNOWN",
            "funding_level": bundle.funding.get("level", "UNKNOWN") if bundle.funding else "UNKNOWN",
            "liquidity_level": bundle.liquidity_context.get("level", "UNKNOWN") if bundle.liquidity_context else "UNKNOWN",
            "market_session": bundle.market_session or "UNKNOWN",
            "intelligence_confidence": bundle.confidence,
            "features_available": bundle.feature_count,
        }
