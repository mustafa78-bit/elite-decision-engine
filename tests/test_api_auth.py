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


def test_refresh_success(api_client, db_session):
    import jwt
    from auth.service import hash_password
    from auth.jwt import _get_secret
    from datetime import datetime, timezone, timedelta

    # Create user
    user = User(username="refreshtest", email="refresh@example.com", hashed_password=hash_password("pass123"))
    db_session.add(user)
    db_session.flush()

    # Generate an active token that is valid but with an early expiry
    # e.g., expires in 5 minutes
    early_exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token_payload = {"sub": str(user.id), "username": user.username, "exp": early_exp}
    original_token = jwt.encode(token_payload, _get_secret(), algorithm="HS256")

    # Call /auth/refresh with original_token
    resp = api_client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {original_token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "token" in body
    assert body["user"]["username"] == "refreshtest"
    assert body["user"]["email"] == "refresh@example.com"
    assert body["user"]["id"] == user.id

    # Decode new token and verify expiry is pushed forward
    new_token = body["token"]
    new_payload = jwt.decode(new_token, _get_secret(), algorithms=["HS256"])
    original_exp_timestamp = int(early_exp.timestamp())
    new_exp_timestamp = new_payload["exp"]
    assert new_exp_timestamp > original_exp_timestamp


def test_refresh_expired_token(api_client, db_session):
    import jwt
    from auth.service import hash_password
    from auth.jwt import _get_secret
    from datetime import datetime, timezone, timedelta

    # Create user
    user = User(username="refreshtest2", email="refresh2@example.com", hashed_password=hash_password("pass123"))
    db_session.add(user)
    db_session.flush()

    # Generate an expired token
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    token_payload = {"sub": str(user.id), "username": user.username, "exp": expired_time}
    expired_token = jwt.encode(token_payload, _get_secret(), algorithm="HS256")

    # Call /auth/refresh
    resp = api_client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert resp.status_code == 401
    assert "Invalid or expired token" in resp.json()["detail"]


def test_refresh_missing_token(api_client):
    if "Authorization" in api_client.headers:
        del api_client.headers["Authorization"]
    resp = api_client.post("/auth/refresh")
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]


def test_refresh_malformed_token(api_client):
    resp = api_client.post(
        "/auth/refresh",
        headers={"Authorization": "Bearer malformed.token.here"}
    )
    assert resp.status_code == 401
    assert "Invalid or expired token" in resp.json()["detail"]


def test_refresh_user_not_found(api_client):
    import jwt
    from auth.jwt import _get_secret
    from datetime import datetime, timezone, timedelta

    # Generate a valid token but for a non-existent user ID
    exp_time = datetime.now(timezone.utc) + timedelta(minutes=10)
    token_payload = {"sub": "999999", "username": "nonexistent", "exp": exp_time}
    token = jwt.encode(token_payload, _get_secret(), algorithm="HS256")

    resp = api_client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 401
    assert "User not found" in resp.json()["detail"]
