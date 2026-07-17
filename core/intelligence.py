from typing import Any, Dict, Optional

from filters.btc_filter import BTCHealthFilter
from decision.fusion import IntelligenceFusion


class IntelligenceBundle:

    def __init__(self):
        self.btc = BTCHealthFilter()
        self.whale = None
        self.liquidity = None
        self.orderflow = None
        self.market_structure = None
        self.news = None
        self.sentiment = None
        self.macro = None
        self.monitoring = {
            "evaluate_calls": 0,
            "modules_active": 0,
        }
        self.fusion = IntelligenceFusion()

    def enable_whale(self, whale_integration) -> None:
        self.whale = whale_integration

    def enable_liquidity(self, liquidity_integration) -> None:
        self.liquidity = liquidity_integration

    def enable_orderflow(self, orderflow_integration) -> None:
        self.orderflow = orderflow_integration

    def enable_market_structure(self, ms_integration) -> None:
        self.market_structure = ms_integration

    def enable_news(self, news_integration) -> None:
        self.news = news_integration

    def enable_sentiment(self, sentiment_integration) -> None:
        self.sentiment = sentiment_integration

    def enable_macro(self, macro_integration) -> None:
        self.macro = macro_integration

    def evaluate(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.monitoring["evaluate_calls"] += 1
        active = 0

        result: Dict[str, Any] = {
            "btc": self.btc.evaluate(data),
        }

        if self.whale and self.whale.enabled:
            result["whale"] = self.whale.evaluate(data)
            active += 1
        else:
            result["whale"] = {"ok": True, "whale_available": False}

        if self.liquidity and self.liquidity.enabled:
            result["liquidity"] = self.liquidity.evaluate(data)
            active += 1
        else:
            result["liquidity"] = {"ok": True, "liquidity_available": False}

        if self.orderflow and self.orderflow.enabled:
            result["orderflow"] = self.orderflow.evaluate(data)
            active += 1
        else:
            result["orderflow"] = {"ok": True, "orderflow_available": False}

        if self.market_structure and self.market_structure.enabled:
            result["market_structure"] = self.market_structure.evaluate(data)
            active += 1
        else:
            result["market_structure"] = {"ok": True, "market_structure_available": False}

        if self.news and self.news.enabled:
            result["news"] = self.news.evaluate(data)
            active += 1
        else:
            result["news"] = {"ok": True, "news_available": False}

        if self.sentiment and self.sentiment.enabled:
            result["sentiment"] = self.sentiment.evaluate(data)
            active += 1
        else:
            result["sentiment"] = {"ok": True, "sentiment_available": False}

        if self.macro and self.macro.enabled:
            result["macro"] = self.macro.evaluate(data)
            active += 1
        else:
            result["macro"] = {"ok": True, "macro_available": False}

        self.monitoring["modules_active"] = active
        result["_monitoring"] = dict(self.monitoring)
        result["_modules"] = {
            "whale": self.whale is not None and self.whale.enabled,
            "liquidity": self.liquidity is not None and self.liquidity.enabled,
            "orderflow": self.orderflow is not None and self.orderflow.enabled,
            "market_structure": self.market_structure is not None and self.market_structure.enabled,
            "news": self.news is not None and self.news.enabled,
            "sentiment": self.sentiment is not None and self.sentiment.enabled,
            "macro": self.macro is not None and self.macro.enabled,
        }

        fusion_result = self.fusion.compute_unified_score(result)
        result["_fusion"] = fusion_result

        return result

    def get_all_features(self) -> Dict[str, Any]:
        features: Dict[str, Any] = {}
        btc_result = self.btc.evaluate()
        features["btc_health"] = btc_result.get("score", 0)

        if self.whale and self.whale.enabled:
            whale_features = self.whale.get_features()
            features["whale"] = whale_features

        if self.liquidity and self.liquidity.enabled:
            liq_features = self.liquidity.get_features()
            features["liquidity"] = liq_features

        if self.orderflow and self.orderflow.enabled:
            of_features = self.orderflow.get_features()
            features["orderflow"] = of_features

        if self.market_structure and self.market_structure.enabled:
            ms_features = self.market_structure.get_features()
            features["market_structure"] = ms_features

        if self.news and self.news.enabled:
            news_features = self.news.get_features()
            features["news"] = news_features

        if self.sentiment and self.sentiment.enabled:
            sent_features = self.sentiment.get_features()
            features["sentiment"] = sent_features

        if self.macro and self.macro.enabled:
            macro_features = self.macro.get_features()
            features["macro"] = macro_features

        return features

    def get_fusion_report(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        eval_result = self.evaluate(data)
        return self.fusion.contribution_report(eval_result)

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "monitoring": dict(self.monitoring),
            "modules": {
                "whale": self.whale is not None and self.whale.enabled,
                "liquidity": self.liquidity is not None and self.liquidity.enabled,
                "orderflow": self.orderflow is not None and self.orderflow.enabled,
                "market_structure": self.market_structure is not None and self.market_structure.enabled,
                "news": self.news is not None and self.news.enabled,
                "sentiment": self.sentiment is not None and self.sentiment.enabled,
                "macro": self.macro is not None and self.macro.enabled,
            },
            "fusion_weights": self.fusion._weights,
        }
