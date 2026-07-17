from decision.confidence import AdaptiveConfidenceEngine, ConfidenceBreakdown, CONFIDENCE_THRESHOLDS


class TestConfidenceBreakdown:

    def test_defaults(self):
        cb = ConfidenceBreakdown()
        assert cb.base_confidence == 50.0
        assert cb.final_confidence == 50.0
        assert cb.components == {}

    def test_to_dict(self):
        cb = ConfidenceBreakdown(final_confidence=75.0)
        d = cb.to_dict()
        assert d["final_confidence"] == 75.0
        assert "timestamp" in d


class TestAdaptiveConfidenceEngine:

    def test_default_calculation(self):
        engine = AdaptiveConfidenceEngine()
        result = engine.calculate()
        assert result.base_confidence == 50.0
        assert result.final_confidence == 55.0
        assert len(engine.history) == 1

    def test_intelligence_contribution_all_healthy(self):
        engine = AdaptiveConfidenceEngine(base_confidence=50.0)
        data = {
            "whale": {"ok": True, "whale_available": True, "features": {"whale_features": {"whale_enabled": True}}},
            "liquidity": {"ok": True, "liquidity_available": True, "features": {"liquidity_features": {"liquidity_enabled": True}}},
            "orderflow": {"ok": True, "orderflow_available": True, "features": {"orderflow_features": {"orderflow_enabled": True}}},
        }
        result = engine.calculate(intelligence_data=data)
        assert result.intelligence_contribution > 0
        assert result.final_confidence > 50.0

    def test_intelligence_contribution_unhealthy(self):
        engine = AdaptiveConfidenceEngine(base_confidence=50.0)
        data = {
            "whale": {"ok": False, "whale_available": False},
        }
        result = engine.calculate(intelligence_data=data)
        assert result.intelligence_contribution < 0

    def test_risk_contribution(self):
        engine = AdaptiveConfidenceEngine()
        result = engine.calculate(risk_score=0.0)
        assert result.risk_contribution == 5.0

    def test_risk_contribution_high(self):
        engine = AdaptiveConfidenceEngine()
        result = engine.calculate(risk_score=30.0)
        assert result.risk_contribution < 0

    def test_regime_contribution_bullish(self):
        engine = AdaptiveConfidenceEngine()
        result = engine.calculate(market_regime="BULLISH")
        assert result.regime_contribution == 10.0

    def test_regime_contribution_bearish(self):
        engine = AdaptiveConfidenceEngine()
        result = engine.calculate(market_regime="BEARISH")
        assert result.regime_contribution == -10.0

    def test_volatility_adjustment_high(self):
        engine = AdaptiveConfidenceEngine()
        result = engine.calculate(volatility=85.0)
        assert result.volatility_adjustment == -10.0

    def test_volatility_adjustment_low(self):
        engine = AdaptiveConfidenceEngine()
        result = engine.calculate(volatility=10.0)
        assert result.volatility_adjustment == 3.0

    def test_liquidity_adjustment(self):
        engine = AdaptiveConfidenceEngine()
        result = engine.calculate(liquidity_score=10.0)
        assert result.liquidity_adjustment == 5.0

    def test_whale_adjustment(self):
        engine = AdaptiveConfidenceEngine()
        result = engine.calculate(whale_score=15.0)
        assert result.whale_adjustment == 6.0

    def test_final_confidence_clamped(self):
        engine = AdaptiveConfidenceEngine(base_confidence=200.0)
        result = engine.calculate()
        assert result.final_confidence <= 100.0

    def test_final_confidence_no_negative(self):
        engine = AdaptiveConfidenceEngine(base_confidence=-50.0)
        result = engine.calculate()
        assert result.final_confidence >= 0.0

    def test_classify_strong_approve(self):
        engine = AdaptiveConfidenceEngine()
        assert engine.classify_confidence(85.0) == "STRONG_APPROVE"

    def test_classify_approve(self):
        engine = AdaptiveConfidenceEngine()
        assert engine.classify_confidence(70.0) == "APPROVE"

    def test_classify_neutral(self):
        engine = AdaptiveConfidenceEngine()
        assert engine.classify_confidence(50.0) == "NEUTRAL"

    def test_classify_caution(self):
        engine = AdaptiveConfidenceEngine()
        assert engine.classify_confidence(30.0) == "CAUTION"

    def test_classify_reject(self):
        engine = AdaptiveConfidenceEngine()
        assert engine.classify_confidence(10.0) == "REJECT"

    def test_validate(self):
        engine = AdaptiveConfidenceEngine()
        assert engine.validate(50.0) is True
        assert engine.validate(-1.0) is False
        assert engine.validate(101.0) is False

    def test_get_confidence_trend_stable(self):
        engine = AdaptiveConfidenceEngine()
        engine.calculate()
        engine.calculate()
        assert engine.get_confidence_trend() == "STABLE"

    def test_get_confidence_trend_rising(self):
        engine = AdaptiveConfidenceEngine()
        engine.calculate()
        engine.base_confidence = 60.0
        engine.calculate()
        assert engine.get_confidence_trend() == "RISING"

    def test_get_confidence_trend_falling(self):
        engine = AdaptiveConfidenceEngine()
        engine.calculate()
        engine.base_confidence = 40.0
        engine.calculate()
        assert engine.get_confidence_trend() == "FALLING"

    def test_get_recent_history(self):
        engine = AdaptiveConfidenceEngine()
        for _ in range(5):
            engine.calculate()
        assert len(engine.get_recent_history(3)) == 3

    def test_reset_history(self):
        engine = AdaptiveConfidenceEngine()
        engine.calculate()
        engine.reset_history()
        assert engine.history == []

    def test_compare_no_history(self):
        e1 = AdaptiveConfidenceEngine()
        e2 = AdaptiveConfidenceEngine()
        result = e1.compare(e2)
        assert "error" in result

    def test_compare_with_history(self):
        e1 = AdaptiveConfidenceEngine()
        e2 = AdaptiveConfidenceEngine()
        e1.calculate()
        e2.calculate()
        result = e1.compare(e2)
        assert "self_confidence" in result
        assert "other_confidence" in result

    def test_prevent_confidence_inflation(self):
        engine = AdaptiveConfidenceEngine(base_confidence=50.0)
        data = {
            "whale": {"ok": True, "whale_available": True, "features": {"whale_features": {"whale_enabled": True}}},
            "liquidity": {"ok": True, "liquidity_available": True, "features": {"liquidity_features": {"liquidity_enabled": True}}},
            "orderflow": {"ok": True, "orderflow_available": True, "features": {"orderflow_features": {"orderflow_enabled": True}}},
            "market_structure": {"ok": True, "market_structure_available": True, "features": {"market_structure_features": {"market_structure_enabled": True}}},
            "news": {"ok": True, "news_available": True, "features": {"news_features": {"news_enabled": True}}},
            "sentiment": {"ok": True, "sentiment_available": True, "features": {"sentiment_features": {"sentiment_enabled": True}}},
            "macro": {"ok": True, "macro_available": True, "features": {"macro_features": {"macro_enabled": True}}},
        }
        result = engine.calculate(intelligence_data=data)
        assert result.final_confidence <= 100.0

    def test_config_limits(self):
        engine = AdaptiveConfidenceEngine()
        assert engine._config["max_intelligence_boost"] <= 30
        assert engine._config["max_risk_penalty"] >= -30
        assert engine._config["max_volatility_penalty"] >= -15
