from auth.jwt import create_access_token
from database import User


def test_register_success(api_client):
    resp = api_client.post("/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "secure123",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "token" in body
    assert body["user"]["username"] == "newuser"


def test_register_duplicate_username(api_client, db_session):
    db_session.add(User(username="dupuser", email="first@example.com", hashed_password="longenoughpassword"))
    db_session.flush()
    resp = api_client.post("/auth/register", json={
        "username": "dupuser",
        "email": "second@example.com",
        "password": "longenoughpassword",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is False
    assert "already exists" in resp.json()["error"]


def test_register_duplicate_email(api_client, db_session):
    db_session.add(User(username="user1", email="dup@example.com", hashed_password="longenoughpassword"))
    db_session.flush()
    resp = api_client.post("/auth/register", json={
        "username": "user2",
        "email": "dup@example.com",
        "password": "longenoughpassword",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is False
    assert "already exists" in resp.json()["error"]


def test_login_success(api_client, db_session):
    from auth.service import hash_password
    db_session.add(User(username="logintest", email="login@example.com", hashed_password=hash_password("pass123")))
    db_session.flush()
    resp = api_client.post("/auth/login", json={
        "username": "logintest",
        "password": "pass123",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "token" in body


def test_login_invalid_password(api_client, db_session):
    from auth.service import hash_password
    db_session.add(User(username="logintest2", email="login2@example.com", hashed_password=hash_password("correctpassword")))
    db_session.flush()
    resp = api_client.post("/auth/login", json={
        "username": "logintest2",
        "password": "wrong",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is False
    assert "Invalid" in resp.json()["error"]


def test_login_nonexistent_user(api_client):
    resp = api_client.post("/auth/login", json={
        "username": "nobody",
        "password": "x",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is False


def test_register_short_password_returns_422_not_500(api_client):
    """The password-length check must be a real Pydantic validator so
    FastAPI's RequestValidationError handler returns 422 -- previously it
    was a plain classmethod called manually inside the route body, so the
    raised ValueError propagated uncaught into the global Exception handler
    and returned a misleading 500 "Internal server error" instead.
    """
    resp = api_client.post("/auth/register", json={
        "username": "shortpw",
        "email": "shortpw@example.com",
        "password": "short",
    })
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert any("at least 8 characters" in str(err.get("msg", "")) for err in detail)
