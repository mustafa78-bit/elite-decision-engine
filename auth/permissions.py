from __future__ import annotations

from auth.models import Role

_ADMIN_ROUTES: set[str] = {
    "POST /kill-switch",
    "POST /resume",
}

_READ_ROUTES: set[str] = {
    "GET /status",
    "GET /health",
    "GET /portfolio",
    "GET /trades",
    "GET /performance",
}

_ALL_ROUTES = _ADMIN_ROUTES | _READ_ROUTES


def _route_key(method: str, path: str) -> str:
    return f"{method.upper()} {path.rstrip('/')}"


def has_permission(role: Role, method: str, path: str) -> bool:
    if role == Role.ADMIN:
        return True
    key = _route_key(method, path)
    if role in (Role.OPERATOR, Role.VIEWER):
        return key in _READ_ROUTES
    return False
