import pytest
from fastapi.testclient import TestClient

from api.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the rate limiter before each rate limiting test."""
    limiter.reset()
    yield
    limiter.reset()

def test_auth_register_rate_limit(api_client: TestClient):
    # /auth/register has a 5/minute rate limit.
    # The first 5 requests should get processed (might return 200, 400 or whatever status,
    # but not 429).
    for i in range(5):
        resp = api_client.post(
            "/auth/register",
            json={
                "username": f"user_reg_{i}",
                "email": f"user_reg_{i}@example.com",
                "password": "valid_password_123"
            }
        )
        assert resp.status_code != 429, f"Request {i} unexpectedly rate limited"

    # The 6th request must be rate limited with HTTP 429.
    resp = api_client.post(
        "/auth/register",
        json={
            "username": "user_reg_6",
            "email": "user_reg_6@example.com",
            "password": "valid_password_123"
        }
    )
    assert resp.status_code == 429
    assert "Too Many Requests" in resp.text or "rate limit exceeded" in resp.text.lower()


def test_auth_login_rate_limit(api_client: TestClient):
    # /auth/login has a 10/minute rate limit.
    # First 10 requests should go through.
    for i in range(10):
        resp = api_client.post(
            "/auth/login",
            json={
                "username": f"user_login_{i}",
                "password": "some_password_123"
            }
        )
        assert resp.status_code != 429, f"Request {i} unexpectedly rate limited"

    # The 11th request must return 429.
    resp = api_client.post(
        "/auth/login",
        json={
            "username": "user_login_11",
            "password": "some_password_123"
        }
    )
    assert resp.status_code == 429


def test_ollo_query_rate_limit(api_client: TestClient, monkeypatch):
    # /ollo/query has a 20/minute rate limit.
    # We should mock get_ollo/query because OLLO calls an external LLM
    # Let's mock the query method on OLLOService to return a dummy OLLOResponse
    # or let the API route return a 503 or 500 when OLLO is not initialized,
    # because rate limiting is processed BEFORE the handler is executed anyway.
    # But to be safe, let's mock it so that it returns 200/ok.
    class DummyResponse:
        def to_dict(self):
            return {"text": "dummy response"}

    class DummyOLLOService:
        def query(self, query: str, room_id: str):
            return DummyResponse()

    monkeypatch.setattr("api.routes.ollo._get_ollo", lambda: DummyOLLOService())

    # Let's make 20 requests
    for i in range(20):
        resp = api_client.post(
            "/ollo/query",
            params={"query": "hello olllo", "room": "command_deck"}
        )
        assert resp.status_code != 429, f"Request {i} unexpectedly rate limited"

    # The 21st request must be rate limited with HTTP 429
    resp = api_client.post(
        "/ollo/query",
        params={"query": "hello olllo", "room": "command_deck"}
    )
    assert resp.status_code == 429
