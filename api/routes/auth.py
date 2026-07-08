from fastapi import APIRouter
from pydantic import BaseModel

from auth.service import login_user, register_user

router = APIRouter()


class AuthRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


@router.post("/auth/register")
def register(body: RegisterRequest):
    return register_user(body.username, body.email, body.password)


@router.post("/auth/login")
def login(body: AuthRequest):
    return login_user(body.username, body.password)
