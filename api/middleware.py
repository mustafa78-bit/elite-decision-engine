import logging
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from auth.jwt import decode_access_token


logger = logging.getLogger(__name__)

# Only these paths are accessible without authentication
PUBLIC_PATHS = frozenset({
    "/health",
    "/auth/register",
    "/auth/login",
})


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

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning("[%s] Auth failure: missing token on %s", rid, path)
        response = JSONResponse(status_code=401, content={"detail": "Authentication required"})
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
