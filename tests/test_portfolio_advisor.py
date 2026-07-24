from __future__ import annotations

import pytest
from datetime import datetime, timezone

from database import Trade, Signal
from services.portfolio_service import PortfolioService


def _make_trade(db_session, **overrides):
    kwargs = dict(
        signal_id=1,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49250.0,
        tp1=51000.0,
        status="OPEN",
        pnl=None,
    )
    kwargs.update(overrides)
    t = Trade(**kwargs)
    db_session.add(t)
    db_session.flush()
    return t


def test_advisor_empty_portfolio(session_factory):
    svc = PortfolioService(session_factory=session_factory)
    adv = svc.advisor()

    assert "health_score" in adv
    assert adv["health_score"] == 100
    assert adv["diversification"]["status"] == "DIVERSIFIED"
    assert adv["diversification"]["concentration_ratio"] == 0.0
    assert len(adv["worst_case_scenarios"]) == 3
    assert len(adv["rebalancing_suggestions"]) >= 1
    assert len(adv["opportunity_recommendations"]) >= 1

    # Product review executive summary asserts
    assert "executive_summary" in adv
    es = adv["executive_summary"]
    assert es["overall_health_score"] == 100
    assert "recommended_action" in es
    assert es["biggest_weakness"] == "No Open Exposure (100% Cash Drag)"
    assert es["biggest_opportunity"] != "None"


def test_advisor_concentrated_portfolio(db_session, session_factory):
    _make_trade(db_session, symbol="BTCUSDT", entry=100000.0, status="OPEN")

    svc = PortfolioService(session_factory=session_factory)
    adv = svc.advisor()

    # Highly concentrated in 1 asset
    assert adv["diversification"]["status"] == "CONCENTRATED"
    assert adv["diversification"]["concentration_ratio"] == 1.0
    assert adv["health_score"] < 100  # should have deducted points

    # Should have a TRIM recommendation with Q&A logic
    trim_suggestions = [s for s in adv["rebalancing_suggestions"] if s["action"] == "TRIM"]
    assert len(trim_suggestions) > 0
    sug = trim_suggestions[0]
    assert "why" in sug
    assert "evidence" in sug
    assert "expected_benefit" in sug


def test_advisor_sector_mapping(db_session, session_factory):
    _make_trade(db_session, symbol="BTCUSDT", entry=50000.0, status="OPEN")
    _make_trade(db_session, symbol="PEPEUSDT", entry=10000.0, status="OPEN")
    _make_trade(db_session, symbol="UNIUSDT", entry=15000.0, status="OPEN")

    svc = PortfolioService(session_factory=session_factory)
    adv = svc.advisor()

    sectors = {s["sector"] for s in adv["sector_exposure"]}
    assert "Layer 1 (Store of Value)" in sectors
    assert "Memes" in sectors
    assert "DeFi" in sectors


def test_advisor_endpoints_registered(api_client):
    resp = api_client.get("/portfolio/advisor")
    assert resp.status_code == 200
    data = resp.json()
    assert "health_score" in data
    assert "diversification" in data
    assert "sector_exposure" in data
    assert "correlation_matrix" in data
    assert "executive_summary" in data

    resp_full = api_client.get("/portfolio/full")
    assert resp_full.status_code == 200
    full_data = resp_full.json()
    assert "advisor" in full_data
    assert "health_score" in full_data["advisor"]
