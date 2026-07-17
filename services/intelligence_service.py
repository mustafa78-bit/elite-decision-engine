from typing import Any, Dict, List, Optional

from core.cache import TTLCache
from core.engine import DecisionEngine
from dto.models import IntelligenceDTO, IntelligenceDetailsDTO, MarketRegimeDTO


class IntelligenceService:

    def __init__(
        self,
        engine: DecisionEngine,
        cache_ttl: float = 30.0,
    ):
        self._engine = engine
        self._cache = TTLCache(default_ttl=cache_ttl)
        self._diagnostics: Dict[str, Any] = {
            "total_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def get_intelligence(self, force_refresh: bool = False) -> IntelligenceDetailsDTO:
        self._diagnostics["total_calls"] += 1
        if not force_refresh:
            cached = self._cache.get("intelligence")
            if cached is not None:
                self._diagnostics["cache_hits"] += 1
                return cached
        self._diagnostics["cache_misses"] += 1

        try:
            result = self._engine.intelligence.evaluate()
            fusion = result.get("_fusion", {})
            report = self._engine.intelligence.get_fusion_report()
            health = fusion.get("health", {})

            summary = IntelligenceDTO(
                unified_score=fusion.get("unified_score", 50.0),
                whale_health=health.get("whale", False),
                liquidity_health=health.get("liquidity", False),
                orderflow_health=health.get("orderflow", False),
                ms_health=health.get("market_structure", False),
                news_health=health.get("news", False),
                sentiment_health=health.get("sentiment", False),
                macro_health=health.get("macro", False),
                module_scores=fusion.get("module_scores", {}),
                contribution_report=report,
            )

            detail = IntelligenceDetailsDTO(
                summary=summary,
                ai_confidence=self._compute_ai_confidence(result),
                funding_summary=self._extract_funding(result),
                open_interest_summary=self._extract_open_interest(result),
                whale_summary=self._extract_whale(result),
                liquidity_summary=self._extract_liquidity(result),
                orderflow_summary=self._extract_orderflow(result),
                market_regime=self._compute_market_regime(result),
                trend_summary=self._extract_trend(result),
                signal_summary=self._extract_signals(result),
            )
            self._cache.set("intelligence", detail)
            return detail
        except Exception:
            return IntelligenceDetailsDTO()

    def _compute_ai_confidence(self, result: Dict[str, Any]) -> float:
        fusion = result.get("_fusion", {})
        return round(fusion.get("unified_score", 50.0), 1)

    def _extract_funding(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result.get("funding", {"available": False, "value": 0, "signal": "neutral"})

    def _extract_open_interest(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result.get("open_interest", {"available": False, "value": 0, "trend": "neutral"})

    def _extract_whale(self, result: Dict[str, Any]) -> Dict[str, Any]:
        whale = result.get("whale", {})
        return {
            "ok": whale.get("ok", False),
            "large_transfers": whale.get("large_transfers", 0),
            "accumulation_score": whale.get("score", 0),
        }

    def _extract_liquidity(self, result: Dict[str, Any]) -> Dict[str, Any]:
        liq = result.get("liquidity", {})
        return {
            "ok": liq.get("ok", False),
            "zones_detected": liq.get("zones", 0),
            "sweep_detected": liq.get("sweep", False),
        }

    def _extract_orderflow(self, result: Dict[str, Any]) -> Dict[str, Any]:
        of = result.get("orderflow", {})
        return {
            "ok": of.get("ok", False),
            "delta": of.get("delta", 0),
            "cvd": of.get("cvd", 0),
        }

    def _compute_market_regime(self, result: Dict[str, Any]) -> MarketRegimeDTO:
        fusion = result.get("_fusion", {})
        score = fusion.get("unified_score", 50.0)
        if score >= 70:
            regime, trend, strength = "bullish", "uptrend", score / 100
        elif score >= 40:
            regime, trend, strength = "neutral", "sideways", score / 100
        else:
            regime, trend, strength = "bearish", "downtrend", score / 100
        return MarketRegimeDTO(regime=regime, trend=trend, strength=round(strength, 2))

    def _extract_trend(self, result: Dict[str, Any]) -> Dict[str, Any]:
        fusion = result.get("_fusion", {})
        return {
            "primary": fusion.get("market_regime", "neutral"),
            "strength": fusion.get("unified_score", 50.0),
            "divergence_detected": False,
        }

    def _extract_signals(self, result: Dict[str, Any]) -> Dict[str, Any]:
        history = self._engine.get_decision_history(n=50)
        approved = sum(1 for h in history if h.get("decision") == "APPROVED")
        rejected = sum(1 for h in history if h.get("decision") == "REJECTED")
        return {
            "total_signals": len(history),
            "approved": approved,
            "rejected": rejected,
            "approval_rate": round(approved / len(history) * 100, 1) if history else 0.0,
        }

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            **self._diagnostics,
        }

    def invalidate_cache(self) -> None:
        self._cache.invalidate("intelligence")
