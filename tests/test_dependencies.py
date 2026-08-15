import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from api.dependencies import _require_user_id, require_user_id


class DummyState:
    pass


class DummyRequest:
    def __init__(self, user_id=None):
        self.state = DummyState()
        if user_id is not None:
            self.state.user_id = user_id


def test_require_user_id_success():
    req = DummyRequest(user_id=42)
    assert require_user_id(req) == 42


def test_require_user_id_missing_attribute():
    req = DummyRequest()
    with pytest.raises(HTTPException) as exc_info:
        require_user_id(req)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


def test_require_user_id_none_or_falsy():
    req = DummyRequest(user_id=None)
    with pytest.raises(HTTPException) as exc_info:
        require_user_id(req)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"

    req_zero = DummyRequest(user_id=0)
    with pytest.raises(HTTPException) as exc_info_zero:
        require_user_id(req_zero)
    assert exc_info_zero.value.status_code == 401
    assert exc_info_zero.value.detail == "Not authenticated"


def test_require_user_id_alias():
    assert _require_user_id is require_user_id


def test_require_user_id_as_fastapi_dependency():
    app = FastAPI()

    @app.get("/test-dep")
    def test_route(user_id: int = Depends(require_user_id)):
        return {"user_id": user_id}

    @app.middleware("http")
    async def mock_auth_middleware(request: Request, call_next):
        if request.headers.get("X-Test-User"):
            request.state.user_id = int(request.headers["X-Test-User"])
        return await call_next(request)

    client = TestClient(app)

    # Without user_id set -> 401
    resp_unauth = client.get("/test-dep")
    assert resp_unauth.status_code == 401
    assert resp_unauth.json()["detail"] == "Not authenticated"

    # With user_id set -> 200
    resp_auth = client.get("/test-dep", headers={"X-Test-User": "123"})
    assert resp_auth.status_code == 200
    assert resp_auth.json() == {"user_id": 123}
