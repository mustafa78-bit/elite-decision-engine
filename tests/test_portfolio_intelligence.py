from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from database import Trade
from services.portfolio_service import PortfolioService


class TestPortfolioIntelligence:

    def test_empty_portfolio_advanced_metrics(self, db_session):
        svc = PortfolioService(session_factory=lambda: db_session)
        full = svc.full_portfolio()

        # Summary checks
        summary = full["summary"]
        assert summary["health_score"] == 100.0
        assert summary["volatility"] == 0.0

        # Risk / Diversification / Correlation checks
        risk = full["risk"]
        assert risk["diversification"]["hhi"] == 0.0
        assert risk["diversification"]["diversification_score"] == 100.0
        assert risk["correlation_matrix"] == {}

        # AI Insights check (should return general fallback alert)
        assert len(risk["ai_insights"]) == 1
        assert risk["ai_insights"][0]["type"] == "GENERAL"

    def test_portfolio_volatility_calculation(self, db_session):
        now = datetime.now(timezone.utc)
        # Seed trade history with returns
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", status="TP_HIT", pnl=100.0, closed_at=now))
        db_session.add(Trade(symbol="ETHUSDT", side="SHORT", status="SL_HIT", pnl=-50.0, closed_at=now))
        db_session.flush()

        svc = PortfolioService(session_factory=lambda: db_session)
        summary = svc.summary()

        # Stdev([100.0, -50.0]) = 106.07
        assert summary["volatility"] == pytest.approx(106.07, abs=0.1)

    def test_correlation_matrix_generation(self, db_session):
        now = datetime.now(timezone.utc)
        # Symbol 1 (correlated perfectly with Symbol 2)
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", status="TP_HIT", pnl=10.0, closed_at=now - timedelta(days=2)))
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", status="TP_HIT", pnl=20.0, closed_at=now - timedelta(days=1)))

        db_session.add(Trade(symbol="ETHUSDT", side="LONG", status="TP_HIT", pnl=10.0, closed_at=now - timedelta(days=2)))
        db_session.add(Trade(symbol="ETHUSDT", side="LONG", status="TP_HIT", pnl=20.0, closed_at=now - timedelta(days=1)))

        db_session.flush()

        svc = PortfolioService(session_factory=lambda: db_session)
        risk = svc.risk_metrics()
        matrix = risk["correlation_matrix"]

        assert "BTCUSDT" in matrix
        assert "ETHUSDT" in matrix
        assert matrix["BTCUSDT"]["ETHUSDT"] == pytest.approx(1.0, abs=0.01)

    def test_diversification_hhi_metrics(self, db_session):
        svc = PortfolioService(session_factory=lambda: db_session)

        # Balanced concentration
        div_balanced = svc._diversification_metrics({"BTC": 0.5, "ETH": 0.5})
        assert div_balanced["hhi"] == 0.5
        assert div_balanced["diversification_status"] == "HIGHLY_CONCENTRATED"
        assert div_balanced["shannon_entropy"] > 0.6

        # Diversified concentration
        div_div = svc._diversification_metrics({"BTC": 0.1, "ETH": 0.1, "SOL": 0.1, "ADA": 0.1, "DOT": 0.1, "AVAX": 0.1, "LINK": 0.1, "XRP": 0.1, "LTC": 0.1, "BCH": 0.1})
        assert div_div["hhi"] == pytest.approx(0.1, abs=0.01)
        assert div_div["diversification_status"] == "HIGHLY_DIVERSIFIED"

    def test_ai_insights_generation(self, db_session):
        svc = PortfolioService(session_factory=lambda: db_session)

        # Scenario 1: High drawdown
        summary = {"win_rate": 50.0, "sharpe_ratio": 0.2, "max_drawdown": 25.0, "total_trades": 5}
        risk_m = {"symbol_concentration": {"BTC": 0.3}}
        div = {"hhi": 0.3, "diversification_score": 50.0}
        matrix = {"BTC": {"ETH": 0.8}}

        insights = svc._generate_ai_insights(summary, risk_m, div, matrix)
        types = [i["type"] for i in insights]

        assert "DRAWDOWN" in types
        assert "CORRELATION" in types
        assert "HEALTH" in types  # Low sharpe
