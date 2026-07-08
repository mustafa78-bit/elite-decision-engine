import logging
import uuid

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from auth.jwt import decode_access_token


logger = logging.getLogger(__name__)

PROTECTED_PATHS = {
    "/portfolio",
    "/risk",
    "/position-sizing",
    "/signals",
    "/performance",
    "/users/me",
    "/users/settings",
}

PUBLIC_PATHS = {"/health", "/auth/register", "/auth/login", "/market", "/market/live", "/monitoring", "/notifications", "/paper-trading", "/execution/status", "/intelligence", "/regime", "/signals/ranking", "/journal", "/backtest", "/trading-control"}


def _generate_request_id() -> str:
    return uuid.uuid4().hex[:12]


async def auth_middleware(request: Request, call_next):
    path = request.url.path
    rid = _generate_request_id()
    request.state.request_id = rid

    if path in PUBLIC_PATHS:
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    if path not in PROTECTED_PATHS:
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning("[%s] Auth failure: missing or malformed token on %s", rid, path)
        response = JSONResponse(status_code=401, content={"detail": "Missing or invalid token"})
        response.headers["X-Request-ID"] = rid
        return response

    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    if payload is None:
        logger.warning("[%s] Auth failure: invalid or expired token on %s", rid, path)
        response = JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})
        response.headers["X-Request-ID"] = rid
        return response

    request.state.user_id = int(payload.get("sub", 0))
    request.state.username = payload.get("username", "")

    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response
