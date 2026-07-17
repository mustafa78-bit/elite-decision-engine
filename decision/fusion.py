from typing import Any, Dict, List, Optional


class IntelligenceFusion:

    def __init__(self):
        self._weights = {
            "whale": 0.15,
            "liquidity": 0.15,
            "orderflow": 0.20,
            "market_structure": 0.20,
            "news": 0.10,
            "sentiment": 0.10,
            "macro": 0.10,
        }
        self._health_status: Dict[str, bool] = {}

    def compute_unified_score(
        self, intelligence_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        scores = {}
        contributions = {}
        total_weight = 0.0
        weighted_sum = 0.0

        for module, weight in self._weights.items():
            module_data = intelligence_data.get(module, {})
            features = module_data.get("features", {})
            module_features = features.get(f"{module}_features", {})

            if isinstance(module_features, dict) and module_features.get(
                f"{module}_enabled", False
            ):
                self._health_status[module] = True
                module_score = self._score_module(module, module_features)
                scores[module] = module_score
                contributions[module] = module_score * weight
                weighted_sum += module_score * weight
                total_weight += weight
            else:
                self._health_status[module] = False
                scores[module] = 50.0
                contributions[module] = 50.0 * weight
                weighted_sum += 50.0 * weight
                total_weight += weight

        unified = weighted_sum / total_weight if total_weight > 0 else 50.0
        unified = max(0.0, min(100.0, unified))

        return {
            "unified_score": unified,
            "module_scores": scores,
            "contributions": contributions,
            "health": dict(self._health_status),
            "weights": dict(self._weights),
        }

    def contribution_report(
        self, intelligence_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        unified_result = self.compute_unified_score(intelligence_data)
        report = {
            "unified_score": unified_result["unified_score"],
            "breakdown": {},
        }
        for module, score in unified_result["module_scores"].items():
            pct_of_total = 0.0
            if unified_result["unified_score"] > 0:
                contrib = unified_result["contributions"].get(module, 0)
                pct_of_total = (contrib / unified_result["unified_score"]) * 100
            report["breakdown"][module] = {
                "raw_score": score,
                "weight": self._weights.get(module, 0),
                "contribution_pct": round(pct_of_total, 1),
                "healthy": unified_result["health"].get(module, False),
            }
        return report

    def _score_module(
        self, module: str, features: Dict[str, Any]
    ) -> float:
        if module == "whale":
            count = features.get("recent_large_transfer_count", 0)
            return min(100.0, 50.0 + count * 5)
        elif module == "liquidity":
            zones = features.get("active_zone_count", 0)
            return min(100.0, 50.0 + zones * 5)
        elif module == "orderflow":
            cvd = features.get("cvd_trend", "NEUTRAL")
            if cvd == "RISING":
                return 70.0
            elif cvd == "FALLING":
                return 30.0
            return 50.0
        elif module == "market_structure":
            trend = features.get("trend", "NEUTRAL")
            if trend == "BULLISH":
                return 70.0
            elif trend == "BEARISH":
                return 30.0
            return 50.0
        elif module == "news":
            sent = features.get("dominant_sentiment", "NEUTRAL")
            if sent == "BULLISH":
                return 65.0
            elif sent == "BEARISH":
                return 35.0
            return 50.0
        elif module == "sentiment":
            bullish = features.get("bullish_assets", 0)
            bearish = features.get("bearish_assets", 0)
            if bullish > bearish:
                return min(100.0, 55.0 + bullish * 3)
            elif bearish > bullish:
                return max(0.0, 45.0 - bearish * 3)
            return 50.0
        elif module == "macro":
            fg = features.get("fear_greed", {})
            classification = fg.get("classification", "NEUTRAL")
            if classification in ("EXTREME_FEAR",):
                return 20.0
            elif classification == "FEAR":
                return 35.0
            elif classification == "GREED":
                return 65.0
            elif classification == "EXTREME_GREED":
                return 80.0
            return 50.0
        return 50.0

    def get_health(self) -> Dict[str, bool]:
        return dict(self._health_status)

    def diagnose(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        for module in self._weights:
            module_data = intelligence_data.get(module, {})
            if not module_data.get("ok", True):
                issues.append(f"{module}: unhealthy")
            features = module_data.get("features", {})
            module_features = features.get(f"{module}_features", {})
            if isinstance(module_features, dict):
                enabled = module_features.get(f"{module}_enabled", False)
                if not enabled:
                    issues.append(f"{module}: disabled")
        return {
            "healthy": len(issues) == 0,
            "issue_count": len(issues),
            "issues": issues,
        }
