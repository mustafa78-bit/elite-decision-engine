from fastapi import APIRouter, Request
from pydantic import BaseModel, field_validator

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

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


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
def refresh(request: Request):
    from auth.jwt import decode_access_token, create_access_token
    from database import User, get_session
    from fastapi import HTTPException

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        new_token = create_access_token({"sub": str(user.id), "username": user.username})
        return {
            "success": True,
            "token": new_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
    finally:
        session.close()
