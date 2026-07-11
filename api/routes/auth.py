from fastapi import APIRouter, Request

from pydantic import BaseModel

from api.rate_limit import limiter
from auth.service import login_user, register_user

router = APIRouter()


class AuthRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


@router.post("/auth/register")
@limiter.limit("3/minute")
def register(request: Request, body: RegisterRequest):
    RegisterRequest.validate_password(body.password)
    return register_user(body.username, body.email, body.password)


@router.post("/auth/login")
@limiter.limit("5/minute")
def login(request: Request, body: AuthRequest):
    return login_user(body.username, body.password)
