from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from auth.jwt import verify_access_token
from auth.models import Role

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Any = Depends(security),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = verify_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload


async def require_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if current_user.get("role") != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_read(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    role = current_user.get("role")
    if role not in (Role.ADMIN.value, Role.OPERATOR.value, Role.VIEWER.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user
