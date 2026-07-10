from __future__ import annotations

import pytest
from database import Signal


def _make_signal(db_session, **overrides):
    kwargs = dict(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN", confidence=85.0, score=0.85)
    kwargs.update(overrides)
    s = Signal(**kwargs)
    db_session.add(s)
    db_session.flush()
    return s


class TestCoordinatorAPI:

    def test_coordinate_nonexistent_returns_404(self, api_client):
        resp = api_client.get("/coordinate/99999")
        assert resp.status_code == 404

    def test_coordinate_signal(self, api_client, db_session):
        signal = _make_signal(db_session)
        resp = api_client.get(f"/coordinate/{signal.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert "report" in body
        assert "consensus" in body["report"]
        assert "aggregations" in body["report"]
        assert "diagnostics" in body["report"]

    def test_coordinate_consensus(self, api_client, db_session):
        signal = _make_signal(db_session)
        resp = api_client.get(f"/coordinate/{signal.id}/consensus")
        assert resp.status_code == 200
        body = resp.json()
        assert "consensus" in body

    def test_list_sources(self, api_client):
        resp = api_client.get("/coordinate/sources")
        assert resp.status_code == 200
        assert "sources" in resp.json()

    def test_coordinate_diagnostics(self, api_client):
        resp = api_client.get("/coordinate/diagnostics")
        assert resp.status_code == 200
        assert "diagnostics" in resp.json()

    def test_register_source(self, api_client):
        resp = api_client.post("/coordinate/sources/register?name=TestSource&source_type=scoring&weight=1.0&priority=5")
        assert resp.status_code == 200
        assert resp.json()["status"] == "registered"

    def test_coordinate_multiple_signals(self, api_client, db_session):
        s1 = _make_signal(db_session, symbol="BTCUSDT")
        s2 = _make_signal(db_session, symbol="ETHUSDT")
        for s in (s1, s2):
            resp = api_client.get(f"/coordinate/{s.id}")
            assert resp.status_code == 200
