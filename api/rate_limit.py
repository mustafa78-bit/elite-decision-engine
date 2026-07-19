import os
from fastapi import Request
from slowapi import Limiter

API_ENV = os.getenv("API_ENV", "development")
# Disable rate limiting in development/testing to avoid blocking login or other endpoints
enabled = (API_ENV == "production")

def resolve_ip(request: Request) -> str:
    # Check for X-Forwarded-For (often contains a comma-separated list, first is client IP)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # Fallback to X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to client host
    if request.client:
        return request.client.host

    return "127.0.0.1"

limiter = Limiter(
    key_func=resolve_ip,
    default_limits=["200/minute"],
    enabled=enabled
)
