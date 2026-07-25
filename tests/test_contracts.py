"""Route contract tests to prevent frontend/backend drift.

Ensures that the core API contracts for auth, preferences, and watchlists
return exact schema and payload keys expected by the React frontend.
"""

from fastapi.testclient import TestClient
from database import User


def _seed_user_id_1(db_session):
    # Ensure a user with id=1 exists to satisfy ForeignKey constraints
    existing = db_session.query(User).filter(User.id == 1).first()
    if not existing:
        u = User(id=1, username="contracttestuser", email="contract1@test.com", hashed_password="hashed_password")
        db_session.add(u)
        db_session.commit()


def test_auth_login_contract(api_client, db_session):
    # Seed a test user
    from auth.service import hash_password

    # Clean users if exist
    db_session.query(User).delete()
    u = User(username="contractuser", email="contract@test.com", hashed_password=hash_password("password123"))
    db_session.add(u)
    db_session.commit()

    # Call login endpoint directly
    from api.main import app
    client = TestClient(app)

    resp = client.post("/auth/login", json={"username": "contractuser", "password": "password123"})
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert isinstance(body, dict)
    assert "token" in body
    assert isinstance(body["token"], str)


def test_preferences_contract(api_client, db_session):
    _seed_user_id_1(db_session)
    resp = api_client.get("/preferences")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert isinstance(body, dict)
    assert "user_id" in body
    assert "timezone" in body
    assert "theme" in body
    assert "dashboard_config" in body
    assert "risk_preferences" in body
    assert "layout_config" in body
    assert "notification_preferences" in body

    assert isinstance(body["dashboard_config"], dict)
    assert isinstance(body["risk_preferences"], dict)
    assert isinstance(body["layout_config"], dict)
    assert isinstance(body["notification_preferences"], dict)


def test_watchlists_contract(api_client, db_session):
    _seed_user_id_1(db_session)
    # Retrieve watchlists list
    resp = api_client.get("/watchlists")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert isinstance(body, dict)
    assert "watchlists" in body
    assert isinstance(body["watchlists"], list)

    # Create a watchlist to verify detail schema contract
    create_resp = api_client.post("/watchlists?name=TestContract&symbols=BTC,ETH")
    assert create_resp.status_code == 200, create_resp.text

    wl = create_resp.json()
    assert "id" in wl
    assert "user_id" in wl
    assert "name" in wl
    assert "symbols" in wl
    assert "created_at" in wl
    assert "updated_at" in wl

    assert wl["name"] == "TestContract"
    assert wl["symbols"] == ["BTC", "ETH"]
