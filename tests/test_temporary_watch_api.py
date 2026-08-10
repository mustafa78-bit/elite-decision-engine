"""Tests for the /watchlist/temporary API routes."""


class TestTemporaryWatchAPI:

    def test_list_empty(self, api_client):
        resp = api_client.get("/watchlist/temporary")
        assert resp.status_code == 200
        assert resp.json() == {"watches": []}

    def test_add_then_list_round_trips(self, api_client):
        resp = api_client.post("/watchlist/temporary?symbol=pepeusdt&days=7&note=breakout")
        assert resp.status_code == 200
        body = resp.json()
        assert body["symbol"] == "PEPEUSDT"
        assert body["note"] == "breakout"

        resp = api_client.get("/watchlist/temporary")
        assert resp.status_code == 200
        watches = resp.json()["watches"]
        assert len(watches) == 1
        assert watches[0]["symbol"] == "PEPEUSDT"

    def test_add_requires_symbol(self, api_client):
        resp = api_client.post("/watchlist/temporary?symbol=&days=7")
        assert resp.status_code == 400

    def test_add_rejects_non_positive_days(self, api_client):
        resp = api_client.post("/watchlist/temporary?symbol=PEPEUSDT&days=0")
        assert resp.status_code == 400

    def test_remove_round_trips(self, api_client):
        api_client.post("/watchlist/temporary?symbol=PEPEUSDT&days=7")
        resp = api_client.delete("/watchlist/temporary/PEPEUSDT")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        resp = api_client.get("/watchlist/temporary")
        assert resp.json() == {"watches": []}

    def test_remove_nonexistent_symbol_404s(self, api_client):
        resp = api_client.delete("/watchlist/temporary/NOPEUSDT")
        assert resp.status_code == 404

    def test_requires_auth(self):
        from fastapi.testclient import TestClient

        from api.main import app

        client = TestClient(app)
        resp = client.get("/watchlist/temporary")
        assert resp.status_code == 401
