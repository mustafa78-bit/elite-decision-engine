import bcrypt

from auth.jwt import create_access_token
from database import User
import database


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def register_user(username: str, email: str, password: str) -> dict:
    session = database.get_session()
    try:
        existing = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return {"success": False, "error": "Username or email already exists"}

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
        )
        session.add(user)
        session.commit()

        token = create_access_token({"sub": str(user.id), "username": username})
        return {"success": True, "token": token, "user": {"id": user.id, "username": username, "email": email}}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()


def login_user(username: str, password: str) -> dict:
    session = database.get_session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return {"success": False, "error": "Invalid username or password"}

        if not verify_password(password, user.hashed_password):
            return {"success": False, "error": "Invalid username or password"}

        token = create_access_token({"sub": str(user.id), "username": user.username})
        return {"success": True, "token": token, "user": {"id": user.id, "username": user.username, "email": user.email}}
    finally:
        session.close()
