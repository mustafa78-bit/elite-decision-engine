from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

from api.rate_limit import limiter
from auth.service import login_user, refresh_session, register_user, revoke_refresh_token

router = APIRouter()


class AuthRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/auth/register")
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest):
    return register_user(body.username, body.email, body.password)


@router.post("/auth/login")
@limiter.limit("10/minute")
def login(request: Request, body: AuthRequest):
    return login_user(body.username, body.password)


@router.post("/auth/refresh")
@limiter.limit("5/minute")
def refresh(request: Request, body: RefreshRequest):
    result = refresh_session(body.refresh_token)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


@router.post("/auth/logout")
@limiter.limit("10/minute")
def logout(request: Request, body: LogoutRequest):
    revoke_refresh_token(body.refresh_token)
    return {"success": True}
