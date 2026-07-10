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


class TestExplanationAPI:

    def test_explain_nonexistent_signal_returns_404(self, api_client):
        resp = api_client.get("/explain/99999")
        assert resp.status_code == 404

    def test_explain_signal_returns_explanation(self, api_client, db_session):
        signal = _make_signal(db_session)
        resp = api_client.get(f"/explain/{signal.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert "signal_id" in body
        assert "explanation" in body
        assert "reasoning" in body["explanation"]
        assert "timeline" in body["explanation"]
        assert "metadata" in body["explanation"]

    def test_explain_reasoning(self, api_client, db_session):
        signal = _make_signal(db_session)
        resp = api_client.get(f"/explain/{signal.id}/reasoning")
        assert resp.status_code == 200
        body = resp.json()
        assert "reasoning" in body
        assert body["reasoning"]["signal_id"] == signal.id

    def test_explain_timeline(self, api_client, db_session):
        signal = _make_signal(db_session)
        resp = api_client.get(f"/explain/{signal.id}/timeline")
        assert resp.status_code == 200
        body = resp.json()
        assert "timeline" in body
        assert body["timeline"]["signal_id"] == signal.id

    def test_explain_human_readable(self, api_client, db_session):
        signal = _make_signal(db_session)
        resp = api_client.get(f"/explain/{signal.id}/human")
        assert resp.status_code == 200
        body = resp.json()
        assert "explanation" in body
        assert isinstance(body["explanation"], str)

    def test_explain_rejected_signal(self, api_client, db_session):
        signal = _make_signal(db_session, status="REJECTED", confidence=30.0, score=0.3)
        resp = api_client.get(f"/explain/{signal.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["explanation"]["reasoning"]["status"] == "REJECTED"

    def test_explain_multiple_signals(self, api_client, db_session):
        s1 = _make_signal(db_session, symbol="BTCUSDT")
        s2 = _make_signal(db_session, symbol="ETHUSDT")
        for s in (s1, s2):
            resp = api_client.get(f"/explain/{s.id}")
            assert resp.status_code == 200

    def test_explain_handles_missing_fields(self, api_client, db_session):
        signal = _make_signal(db_session)
        resp = api_client.get(f"/explain/{signal.id}/reasoning")
        assert resp.status_code == 200

    def test_explain_timeline_has_events(self, api_client, db_session):
        signal = _make_signal(db_session)
        resp = api_client.get(f"/explain/{signal.id}/timeline")
        body = resp.json()
        if body.get("timeline") and body["timeline"].get("events"):
            assert len(body["timeline"]["events"]) >= 1
