from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from auth.jwt import decode_access_token

PROTECTED_PATHS = {
    "/portfolio",
    "/risk",
    "/position-sizing",
    "/signals",
    "/performance",
    "/users/me",
    "/users/settings",
}

PUBLIC_PATHS = {"/health", "/auth/register", "/auth/login", "/market", "/market/live", "/monitoring", "/notifications", "/paper-trading", "/execution/status", "/intelligence", "/regime", "/signals/ranking", "/journal", "/backtest"}


async def auth_middleware(request: Request, call_next):
    path = request.url.path

    if path in PUBLIC_PATHS:
        return await call_next(request)

    if path not in PROTECTED_PATHS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid token"})

    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    if payload is None:
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

    request.state.user_id = int(payload.get("sub", 0))
    request.state.username = payload.get("username", "")

    return await call_next(request)
