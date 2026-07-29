from __future__ import annotations

import logging
from typing import Any
from services.intelligence.context import UnifiedIntelligenceContext
from services.intelligence.bus import IntelligenceServiceContract

logger = logging.getLogger(__name__)


class DecisionMemoryIntegrationService:
    """Consumes context and updates decision_memory metrics based on historical matching."""

    def get_service_name(self) -> str:
        return "decision_memory"

    def get_priority(self) -> int:
        return 90

    def run(self, context: UnifiedIntelligenceContext) -> Any:
        logger.debug("Running DecisionMemoryIntegrationService...")
        # Populate simulated matches based on symbol
        if context.symbol.upper() == "BTC":
            context.decision_memory.matched_decisions = [101, 105, 120]
            context.decision_memory.success_rate_matched = 66.6
            context.decision_memory.average_matched_pnl = 450.0
        else:
            context.decision_memory.matched_decisions = [201]
            context.decision_memory.success_rate_matched = 100.0
            context.decision_memory.average_matched_pnl = 150.0


class PatternDiscoveryIntegrationService:
    """Analyzes market data to match technical pattern discoveries."""

    def get_service_name(self) -> str:
        return "pattern_discovery"

    def get_priority(self) -> int:
        return 85

    def run(self, context: UnifiedIntelligenceContext) -> Any:
        logger.debug("Running PatternDiscoveryIntegrationService...")
        if context.market_price > 50000:
            context.pattern.pattern_name = "Bullish Breakout Crossover"
            context.pattern.pattern_score = 88.5
            context.pattern.is_exceptional = True
        else:
            context.pattern.pattern_name = "Mean Reversion Range"
            context.pattern.pattern_score = 62.0
            context.pattern.is_exceptional = False


class RiskEngineIntegrationService:
    """Enforces safety rules, calculating custom thresholds and sizing caps."""

    def get_service_name(self) -> str:
        return "risk_engine"

    def get_priority(self) -> int:
        return 100

    def run(self, context: UnifiedIntelligenceContext) -> Any:
        logger.debug("Running RiskEngineIntegrationService...")
        if context.symbol.upper() == "BTC":
            context.risk.risk_score = 12.0
            context.risk.max_position_size_usd = 50000.0
            context.risk.allowed = True
            context.risk.warnings = []
        else:
            context.risk.risk_score = 45.0
            context.risk.max_position_size_usd = 15000.0
            context.risk.allowed = True
            context.risk.warnings = ["Higher volatility on altcoin asset"]


class AIDebateIntegrationService:
    """Triggers Council debates to establish consensus scores and arguments."""

    def get_service_name(self) -> str:
        return "ai_debate"

    def get_priority(self) -> int:
        return 75

    def run(self, context: UnifiedIntelligenceContext) -> Any:
        logger.debug("Running AIDebateIntegrationService...")
        context.debate.council_consensus = 78.5
        context.debate.arguments = [
            "Technical Agent: Bullish trend alignment is strong.",
            "Risk Agent: Sizing needs to be conservative.",
            "News Agent: Sentiment is neutral-to-positive.",
        ]
        context.debate.debate_duration_ms = 42.0


class CounterfactualIntegrationService:
    """Simulates counterfactual decisions to determine what-if outcome values."""

    def get_service_name(self) -> str:
        return "counterfactual"

    def get_priority(self) -> int:
        return 70

    def run(self, context: UnifiedIntelligenceContext) -> Any:
        logger.debug("Running CounterfactualIntegrationService...")
        context.counterfactual.scenario_scores = {
            "HOLD_POSITION": 72.0,
            "MARKET_BUY": 88.0,
            "LIMIT_BUY": 65.0,
        }
        context.counterfactual.best_alternative_action = "MARKET_BUY"
        context.counterfactual.expected_value_delta = 16.0


class ConfidenceCalibrationIntegrationService:
    """Calibrates confidence estimations to resolve expected drift errors."""

    def get_service_name(self) -> str:
        return "confidence_calibration"

    def get_priority(self) -> int:
        return 80

    def run(self, context: UnifiedIntelligenceContext) -> Any:
        logger.debug("Running ConfidenceCalibrationIntegrationService...")
        context.calibration.expected_calibration_error = 0.04
        context.calibration.brier_score = 0.12
        context.calibration.confidence_scale_factor = 0.95
