"""Shared FastAPI dependencies for API routes."""

from fastapi import HTTPException, Request


def require_user_id(request: Request) -> int:
    """Extract and validate the authenticated user_id from request.state.

    Raises:
        HTTPException(401): If user_id is missing or falsy in request.state.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


# Alias for backward compatibility or alternate naming preference
_require_user_id = require_user_id
