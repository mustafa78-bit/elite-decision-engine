from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from auth.models import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
) -> TokenResponse:
    service = request.app.state.auth_service
    user = service.authenticate(body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return service.create_tokens(user)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    body: dict,
    request: Request,
) -> TokenResponse:
    refresh_token_str = body.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token is required",
        )
    service = request.app.state.auth_service
    result = service.refresh_access_token(refresh_token_str)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return result
