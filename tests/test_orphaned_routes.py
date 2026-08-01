from unittest.mock import MagicMock
import pytest


def test_get_council_reachable(api_client):
    """Test that GET /council is reachable and returns status 200."""
    resp = api_client.get("/council")
    assert resp.status_code == 200
    body = resp.json()
    assert "agent_count" in body
    assert "agents" in body


def test_get_council_evaluate_signal_not_found(api_client):
    """Test that GET /council/evaluate/{signal_id} is reachable.

    Evaluating a non-existent signal ID should return 404 with the specific detail
    indicating the endpoint was reached and processed.
    """
    resp = api_client.get("/council/evaluate/99999")
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body
    assert "signal 99999 not found" in body["detail"].lower()


def test_post_council_evaluate_direct_validation(api_client):
    """Test that POST /council/evaluate is reachable.

    Sending a request without the required symbol query parameter should return 422,
    confirming the endpoint is registered and evaluated by the router.
    """
    resp = api_client.post("/council/evaluate")
    assert resp.status_code == 422


def test_get_whale_activity_reachable(api_client, monkeypatch):
    """Test that GET /whale/activity is reachable and returns a list.

    We mock the MarketDataService to return empty assets to prevent live network queries
    and check that it returns a valid response.
    """
    class FakeAsset:
        is_empty = True
        price = 0.0
        indicators = {}

    class FakeMIP:
        def get_asset(self, sym):
            return FakeAsset()

    # Mock the internal _mip_service inside api/routes/whale.py
    monkeypatch.setattr("api.routes.whale._mip_service", FakeMIP())

    resp = api_client.get("/whale/activity")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
