from typing import Any, Dict, Optional

from core.intelligence import IntelligenceBundle
from decision.confidence import AdaptiveConfidenceEngine


class ScoringEngine:

    def __init__(
        self,
        intelligence: Optional[IntelligenceBundle] = None,
        confidence_engine: Optional[AdaptiveConfidenceEngine] = None,
    ):
        self.intelligence = intelligence or IntelligenceBundle()
        self.confidence_engine = confidence_engine or AdaptiveConfidenceEngine()

    def score_signal(
        self,
        signal_data: Dict[str, Any],
        intelligence_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        score = signal_data.get("base_score", 0)
        whale_boost = 0
        liquidity_boost = 0
        orderflow_boost = 0
        ms_boost = 0
        news_boost = 0
        sentiment_boost = 0
        macro_boost = 0

        if intelligence_data:
            whale_data = intelligence_data.get("whale", {})
            liq_data = intelligence_data.get("liquidity", {})
            of_data = intelligence_data.get("orderflow", {})
            ms_data = intelligence_data.get("market_structure", {})
            news_data = intelligence_data.get("news", {})
            sent_data = intelligence_data.get("sentiment", {})
            macro_data = intelligence_data.get("macro", {})

            whale_features = whale_data.get("features", {}).get("whale_features", {})
            liq_features = liq_data.get("features", {}).get("liquidity_features", {})
            of_features = of_data.get("features", {}).get("orderflow_features", {})
            ms_features = ms_data.get("features", {}).get("market_structure_features", {})
            news_features = news_data.get("features", {}).get("news_features", {})
            sent_features = sent_data.get("features", {}).get("sentiment_features", {})
            macro_features = macro_data.get("features", {}).get("macro_features", {})

            if whale_features.get("whale_enabled", False):
                whale_boost = min(
                    whale_features.get("recent_large_transfer_count", 0) * 2,
                    15,
                )
                score += whale_boost

            if liq_features.get("active_zone_count", 0) > 0:
                liquidity_boost = min(
                    liq_features.get("active_zone_count", 0) * 1.5,
                    10,
                )
                score += liquidity_boost

            if of_features.get("orderflow_enabled", False):
                cvd_trend = of_features.get("cvd_trend", "NEUTRAL")
                if cvd_trend == "RISING":
                    orderflow_boost = 5
                    score += orderflow_boost
                elif cvd_trend == "FALLING":
                    orderflow_boost = -5
                    score += orderflow_boost

            if ms_features.get("market_structure_enabled", False):
                trend = ms_features.get("trend", "NEUTRAL")
                if trend == "BULLISH":
                    ms_boost = 5
                    score += ms_boost
                elif trend == "BEARISH":
                    ms_boost = -5
                    score += ms_boost

            if news_features.get("news_enabled", False):
                dominant = news_features.get("dominant_sentiment")
                if dominant == "BULLISH":
                    news_boost = 3
                    score += news_boost
                elif dominant == "BEARISH":
                    news_boost = -3
                    score += news_boost

            if sent_features.get("sentiment_enabled", False):
                bullish = sent_features.get("bullish_assets", 0)
                bearish = sent_features.get("bearish_assets", 0)
                if bullish > bearish:
                    sentiment_boost = min(bullish * 2, 8)
                    score += sentiment_boost
                elif bearish > bullish:
                    sentiment_boost = -min(bearish * 2, 8)
                    score += sentiment_boost

            if macro_features.get("macro_enabled", False):
                fg = macro_features.get("fear_greed", {})
                classification = fg.get("classification", "NEUTRAL")
                if classification in ("EXTREME_FEAR", "FEAR"):
                    macro_boost = -4
                    score += macro_boost
                elif classification in ("EXTREME_GREED", "GREED"):
                    macro_boost = 3
                    score += macro_boost

        final_score = min(max(score, 0), 100)
        boost_map = {
            "whale": whale_boost,
            "liquidity": liquidity_boost,
            "orderflow": orderflow_boost,
            "market_structure": ms_boost,
            "news": news_boost,
            "sentiment": sentiment_boost,
            "macro": macro_boost,
        }

        confidence = self.confidence_engine.calculate(
            intelligence_data=intelligence_data,
        )

        return {
            "score": final_score,
            "whale_used": intelligence_data is not None and "whale" in intelligence_data,
            "liquidity_used": intelligence_data is not None and "liquidity" in intelligence_data,
            "orderflow_used": intelligence_data is not None and "orderflow" in intelligence_data,
            "market_structure_used": intelligence_data is not None and "market_structure" in intelligence_data,
            "news_used": intelligence_data is not None and "news" in intelligence_data,
            "sentiment_used": intelligence_data is not None and "sentiment" in intelligence_data,
            "macro_used": intelligence_data is not None and "macro" in intelligence_data,
            "boosts": {
                "whale": whale_boost > 0,
                "liquidity": liquidity_boost > 0,
                "orderflow": orderflow_boost != 0,
                "market_structure": ms_boost != 0,
                "news": news_boost != 0,
                "sentiment": sentiment_boost != 0,
                "macro": macro_boost != 0,
            },
            "boost_values": boost_map,
            "confidence_breakdown": confidence.to_dict(),
            "confidence_label": self.confidence_engine.classify_confidence(
                confidence.final_confidence
            ),
        }
