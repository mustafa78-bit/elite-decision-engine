from decision.fusion import IntelligenceFusion


def _make_intel_data(modules=None):
    data = {
        "btc": {"ok": True, "score": 1.0},
        "whale": {"whale_available": False},
        "liquidity": {"liquidity_available": False},
        "orderflow": {"orderflow_available": False},
        "market_structure": {"market_structure_available": False},
        "news": {"news_available": False},
        "sentiment": {"sentiment_available": False},
        "macro": {"macro_available": False},
    }
    if modules:
        for mod, features in modules.items():
            data[mod] = {
                "ok": True,
                f"{mod}_available": True,
                "features": {f"{mod}_features": features},
            }
    return data


class TestIntelligenceFusion:

    def test_default_weights(self):
        fusion = IntelligenceFusion()
        assert len(fusion._weights) == 7
        total = sum(fusion._weights.values())
        assert abs(total - 1.0) < 0.01

    def test_compute_unified_no_modules(self):
        fusion = IntelligenceFusion()
        result = fusion.compute_unified_score(_make_intel_data())
        assert 0 <= result["unified_score"] <= 100
        assert result["health"]["whale"] is False

    def test_compute_unified_whale_active(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"whale": {"whale_enabled": True, "recent_large_transfer_count": 5}})
        result = fusion.compute_unified_score(data)
        assert result["module_scores"]["whale"] > 50

    def test_compute_unified_orderflow_rising(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"orderflow": {"orderflow_enabled": True, "cvd_trend": "RISING"}})
        result = fusion.compute_unified_score(data)
        assert result["module_scores"]["orderflow"] == 70.0

    def test_compute_unified_orderflow_falling(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"orderflow": {"orderflow_enabled": True, "cvd_trend": "FALLING"}})
        result = fusion.compute_unified_score(data)
        assert result["module_scores"]["orderflow"] == 30.0

    def test_compute_unified_ms_bullish(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"market_structure": {"market_structure_enabled": True, "trend": "BULLISH"}})
        result = fusion.compute_unified_score(data)
        assert result["module_scores"]["market_structure"] == 70.0

    def test_compute_unified_macro_extreme_fear(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"macro": {"macro_enabled": True, "fear_greed": {"classification": "EXTREME_FEAR"}}})
        result = fusion.compute_unified_score(data)
        assert result["module_scores"]["macro"] == 20.0

    def test_compute_unified_macro_extreme_greed(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"macro": {"macro_enabled": True, "fear_greed": {"classification": "EXTREME_GREED"}}})
        result = fusion.compute_unified_score(data)
        assert result["module_scores"]["macro"] == 80.0

    def test_compute_unified_news_bullish(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"news": {"news_enabled": True, "dominant_sentiment": "BULLISH"}})
        result = fusion.compute_unified_score(data)
        assert result["module_scores"]["news"] == 65.0

    def test_compute_unified_news_bearish(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"news": {"news_enabled": True, "dominant_sentiment": "BEARISH"}})
        result = fusion.compute_unified_score(data)
        assert result["module_scores"]["news"] == 35.0

    def test_compute_unified_sentiment_bullish(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"sentiment": {"sentiment_enabled": True, "bullish_assets": 5, "bearish_assets": 0}})
        result = fusion.compute_unified_score(data)
        assert result["module_scores"]["sentiment"] == 70.0

    def test_compute_unified_all_trend_bullish(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({
            "whale": {"whale_enabled": True, "recent_large_transfer_count": 3},
            "liquidity": {"liquidity_enabled": True, "active_zone_count": 4},
            "orderflow": {"orderflow_enabled": True, "cvd_trend": "RISING"},
            "market_structure": {"market_structure_enabled": True, "trend": "BULLISH"},
            "news": {"news_enabled": True, "dominant_sentiment": "BULLISH"},
            "sentiment": {"sentiment_enabled": True, "bullish_assets": 2, "bearish_assets": 0},
            "macro": {"macro_enabled": True, "fear_greed": {"classification": "GREED", "value": 70}},
        })
        result = fusion.compute_unified_score(data)
        assert result["unified_score"] > 50

    def test_contribution_report(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"whale": {"whale_enabled": True, "recent_large_transfer_count": 5}})
        report = fusion.contribution_report(data)
        assert "unified_score" in report
        assert "breakdown" in report
        assert "whale" in report["breakdown"]

    def test_diagnosis_healthy(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({
            "whale": {"whale_enabled": True, "recent_large_transfer_count": 1},
        })
        diag = fusion.diagnose(data)
        assert isinstance(diag["healthy"], bool)

    def test_diagnosis_unhealthy_module(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data()
        data["whale"] = {"ok": False, "whale_available": False}
        diag = fusion.diagnose(data)
        assert diag["healthy"] is False
        assert diag["issue_count"] > 0

    def test_get_health(self):
        fusion = IntelligenceFusion()
        data = _make_intel_data({"whale": {"whale_enabled": True, "recent_large_transfer_count": 1}})
        fusion.compute_unified_score(data)
        health = fusion.get_health()
        assert "whale" in health
