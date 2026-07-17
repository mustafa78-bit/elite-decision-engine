import pytest
from unittest.mock import MagicMock, patch

from services.intelligence_service import IntelligenceService


class TestIntelligenceService:

    @pytest.fixture
    def mock_engine(self):
        engine = MagicMock()
        engine.intelligence.evaluate.return_value = {
            "_fusion": {
                "unified_score": 75.0,
                "health": {
                    "whale": True, "liquidity": True, "orderflow": True,
                    "market_structure": True, "news": True, "sentiment": True, "macro": True,
                },
                "module_scores": {"whale": 80.0, "liquidity": 70.0},
                "market_regime": "bullish",
            },
            "funding": {"available": True, "value": 0.01, "signal": "positive"},
            "open_interest": {"available": True, "value": 1000, "trend": "rising"},
            "whale": {"ok": True, "large_transfers": 5, "score": 80},
            "liquidity": {"ok": True, "zones": 3, "sweep": False},
            "orderflow": {"ok": True, "delta": 150, "cvd": 200},
        }
        engine.intelligence.get_fusion_report.return_value = {"modules": {"whale": "active"}}
        engine.get_decision_history.return_value = [
            {"decision": "APPROVED", "score": 80},
            {"decision": "APPROVED", "score": 75},
            {"decision": "REJECTED", "score": 30},
        ]
        return engine

    def _make_service(self, engine):
        return IntelligenceService(engine=engine)

    def test_get_intelligence(self, mock_engine):
        svc = self._make_service(mock_engine)
        detail = svc.get_intelligence()
        assert detail.summary.unified_score == 75.0
        assert detail.summary.whale_health is True
        assert detail.summary.liquidity_health is True
        assert detail.ai_confidence == 75.0
        assert detail.funding_summary["available"] is True
        assert detail.open_interest_summary["available"] is True
        assert detail.whale_summary["ok"] is True
        assert detail.liquidity_summary["ok"] is True
        assert detail.orderflow_summary["ok"] is True

    def test_market_regime_bullish(self, mock_engine):
        svc = self._make_service(mock_engine)
        detail = svc.get_intelligence()
        assert detail.market_regime.regime == "bullish"
        assert detail.market_regime.trend == "uptrend"

    def test_market_regime_neutral(self, mock_engine):
        mock_engine.intelligence.evaluate.return_value = {
            "_fusion": {"unified_score": 50.0, "health": {}, "module_scores": {}},
        }
        mock_engine.intelligence.get_fusion_report.return_value = {}
        svc = self._make_service(mock_engine)
        detail = svc.get_intelligence()
        assert detail.market_regime.regime == "neutral"

    def test_market_regime_bearish(self, mock_engine):
        mock_engine.intelligence.evaluate.return_value = {
            "_fusion": {"unified_score": 20.0, "health": {}, "module_scores": {}},
        }
        mock_engine.intelligence.get_fusion_report.return_value = {}
        svc = self._make_service(mock_engine)
        detail = svc.get_intelligence()
        assert detail.market_regime.regime == "bearish"

    def test_signal_summary(self, mock_engine):
        svc = self._make_service(mock_engine)
        detail = svc.get_intelligence()
        assert detail.signal_summary["total_signals"] == 3
        assert detail.signal_summary["approved"] == 2
        assert detail.signal_summary["rejected"] == 1
        assert detail.signal_summary["approval_rate"] == 66.7

    def test_cache_hit(self, mock_engine):
        svc = self._make_service(mock_engine)
        svc.get_intelligence()
        svc.get_intelligence()
        assert svc.get_diagnostics()["cache_hits"] >= 1

    def test_force_refresh(self, mock_engine):
        svc = self._make_service(mock_engine)
        svc.get_intelligence()
        hits_before = svc.get_diagnostics()["cache_hits"]
        svc.get_intelligence(force_refresh=True)
        assert svc.get_diagnostics()["cache_hits"] == hits_before

    def test_invalidate_cache(self, mock_engine):
        svc = self._make_service(mock_engine)
        svc.get_intelligence()
        svc.invalidate_cache()
        hits_before = svc.get_diagnostics()["cache_hits"]
        svc.get_intelligence()
        assert svc.get_diagnostics()["cache_hits"] == hits_before

    def test_get_diagnostics(self, mock_engine):
        svc = self._make_service(mock_engine)
        diag = svc.get_diagnostics()
        assert "total_calls" in diag
        assert "cache_hits" in diag

    def test_error_fallback(self, mock_engine):
        mock_engine.intelligence.evaluate.side_effect = Exception("evaluation failed")
        svc = self._make_service(mock_engine)
        detail = svc.get_intelligence()
        assert detail.summary.unified_score == 50.0
        assert detail.market_regime.regime == "neutral"

    def test_trend_summary(self, mock_engine):
        svc = self._make_service(mock_engine)
        detail = svc.get_intelligence()
        assert detail.trend_summary["primary"] == "bullish"
        assert detail.trend_summary["strength"] == 75.0
