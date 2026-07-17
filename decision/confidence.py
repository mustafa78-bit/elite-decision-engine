from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


CONFIDENCE_THRESHOLDS = {
    "STRONG_APPROVE": 80.0,
    "APPROVE": 60.0,
    "NEUTRAL": 40.0,
    "CAUTION": 20.0,
    "REJECT": 0.0,
}


@dataclass
class ConfidenceBreakdown:
    base_confidence: float = 50.0
    intelligence_contribution: float = 0.0
    risk_contribution: float = 0.0
    regime_contribution: float = 0.0
    volatility_adjustment: float = 0.0
    liquidity_adjustment: float = 0.0
    whale_adjustment: float = 0.0
    final_confidence: float = 50.0
    components: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_confidence": self.base_confidence,
            "intelligence_contribution": self.intelligence_contribution,
            "risk_contribution": self.risk_contribution,
            "regime_contribution": self.regime_contribution,
            "volatility_adjustment": self.volatility_adjustment,
            "liquidity_adjustment": self.liquidity_adjustment,
            "whale_adjustment": self.whale_adjustment,
            "final_confidence": self.final_confidence,
            "components": dict(self.components),
            "timestamp": self.timestamp.isoformat(),
        }


class AdaptiveConfidenceEngine:

    def __init__(self, base_confidence: float = 50.0):
        self.base_confidence = base_confidence
        self.history: List[ConfidenceBreakdown] = []
        self._config = {
            "max_intelligence_boost": 25.0,
            "max_risk_penalty": -20.0,
            "max_regime_boost": 15.0,
            "max_volatility_penalty": -10.0,
            "liquidity_boost_max": 8.0,
            "whale_boost_max": 10.0,
            "decay_rate": 0.95,
        }

    def calculate(
        self,
        intelligence_data: Optional[Dict[str, Any]] = None,
        risk_score: float = 0.0,
        market_regime: str = "NEUTRAL",
        volatility: float = 0.0,
        liquidity_score: float = 0.0,
        whale_score: float = 0.0,
    ) -> ConfidenceBreakdown:
        breakdown = ConfidenceBreakdown(base_confidence=self.base_confidence)

        intelligence_contrib = self._calculate_intelligence_contribution(
            intelligence_data
        )
        breakdown.intelligence_contribution = min(
            intelligence_contrib, self._config["max_intelligence_boost"]
        )

        risk_contrib = self._calculate_risk_contribution(risk_score)
        breakdown.risk_contribution = max(
            risk_contrib, self._config["max_risk_penalty"]
        )

        regime_contrib = self._calculate_regime_contribution(market_regime)
        breakdown.regime_contribution = min(
            regime_contrib, self._config["max_regime_boost"]
        )

        vol_adj = self._calculate_volatility_adjustment(volatility)
        breakdown.volatility_adjustment = max(
            vol_adj, self._config["max_volatility_penalty"]
        )

        liq_adj = self._calculate_liquidity_adjustment(liquidity_score)
        breakdown.liquidity_adjustment = min(
            liq_adj, self._config["liquidity_boost_max"]
        )

        whale_adj = self._calculate_whale_adjustment(whale_score)
        breakdown.whale_adjustment = min(
            whale_adj, self._config["whale_boost_max"]
        )

        breakdown.components = {
            "intelligence": breakdown.intelligence_contribution,
            "risk": breakdown.risk_contribution,
            "regime": breakdown.regime_contribution,
            "volatility": breakdown.volatility_adjustment,
            "liquidity": breakdown.liquidity_adjustment,
            "whale": breakdown.whale_adjustment,
        }

        cumulative = (
            breakdown.base_confidence
            + breakdown.intelligence_contribution
            + breakdown.risk_contribution
            + breakdown.regime_contribution
            + breakdown.volatility_adjustment
            + breakdown.liquidity_adjustment
            + breakdown.whale_adjustment
        )

        breakdown.final_confidence = max(0.0, min(100.0, cumulative))
        breakdown.timestamp = datetime.now(timezone.utc)
        self.history.append(breakdown)
        return breakdown

    def classify_confidence(self, confidence: float) -> str:
        if confidence >= CONFIDENCE_THRESHOLDS["STRONG_APPROVE"]:
            return "STRONG_APPROVE"
        elif confidence >= CONFIDENCE_THRESHOLDS["APPROVE"]:
            return "APPROVE"
        elif confidence >= CONFIDENCE_THRESHOLDS["NEUTRAL"]:
            return "NEUTRAL"
        elif confidence >= CONFIDENCE_THRESHOLDS["CAUTION"]:
            return "CAUTION"
        else:
            return "REJECT"

    def compare(self, other: "AdaptiveConfidenceEngine") -> Dict[str, Any]:
        if not self.history or not other.history:
            return {"error": "One or both engines have no history"}
        recent_self = self.history[-1].final_confidence
        recent_other = other.history[-1].final_confidence
        return {
            "self_confidence": recent_self,
            "other_confidence": recent_other,
            "difference": recent_self - recent_other,
        }

    def validate(self, confidence: float) -> bool:
        return 0.0 <= confidence <= 100.0

    def get_confidence_trend(self, window: int = 5) -> str:
        if len(self.history) < 2:
            return "STABLE"
        recent = self.history[-window:]
        if len(recent) < 2:
            return "STABLE"
        first = recent[0].final_confidence
        last = recent[-1].final_confidence
        diff = last - first
        if diff > 5:
            return "RISING"
        elif diff < -5:
            return "FALLING"
        return "STABLE"

    def _calculate_intelligence_contribution(
        self, intelligence_data: Optional[Dict[str, Any]] = None
    ) -> float:
        if not intelligence_data:
            return 0.0
        contribution = 0.0
        for module_key in ("whale", "liquidity", "orderflow", "market_structure", "news", "sentiment", "macro"):
            module = intelligence_data.get(module_key, {})
            if module.get("ok", False) is False:
                contribution -= 2.0
            if module.get(f"{module_key}_available", False):
                features = module.get("features", {}).get(f"{module_key}_features", {})
                if isinstance(features, dict):
                    if features.get("whale_enabled", False) or features.get(f"{module_key}_enabled", False):
                        contribution += 3.0
        return contribution

    def _calculate_risk_contribution(self, risk_score: float) -> float:
        if risk_score <= 0:
            return 5.0
        return max(-15.0, 5.0 - risk_score)

    def _calculate_regime_contribution(self, market_regime: str) -> float:
        regime_map = {
            "STRONG_BULLISH": 15.0,
            "BULLISH": 10.0,
            "NEUTRAL": 0.0,
            "BEARISH": -10.0,
            "STRONG_BEARISH": -15.0,
        }
        return regime_map.get(market_regime.upper(), 0.0)

    def _calculate_volatility_adjustment(self, volatility: float) -> float:
        if volatility <= 0:
            return 0.0
        if volatility > 80:
            return -10.0
        elif volatility > 60:
            return -5.0
        elif volatility < 20:
            return 3.0
        return 0.0

    def _calculate_liquidity_adjustment(self, liquidity_score: float) -> float:
        if liquidity_score <= 0:
            return 0.0
        return min(liquidity_score * 0.5, 8.0)

    def _calculate_whale_adjustment(self, whale_score: float) -> float:
        if whale_score <= 0:
            return 0.0
        return min(whale_score * 0.4, 10.0)

    def get_recent_history(self, n: int = 10) -> List[ConfidenceBreakdown]:
        return self.history[-n:]

    def reset_history(self) -> None:
        self.history.clear()
