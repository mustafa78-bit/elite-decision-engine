import time
import uuid
from typing import Any, Callable, Dict, Optional

from api.errors import APIException
from api.schemas import APIResponse, APIError


def generate_request_id() -> str:
    return uuid.uuid4().hex[:12]


class RequestTimingMiddleware:

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request) -> Dict[str, Any]:
        start = time.time()
        response = self.get_response(request)
        elapsed = time.time() - start
        if isinstance(response, dict):
            response["_timing_ms"] = round(elapsed * 1000, 2)
        return response


def error_handler(request, exc, request_id: str = "") -> Dict[str, Any]:
    if isinstance(exc, APIException):
        return APIResponse(
            success=False,
            error=APIError(code=exc.code, message=exc.message, details=exc.details),
            request_id=request_id,
        ).to_dict()
    return APIResponse(
        success=False,
        error=APIError(code="UNEXPECTED_ERROR", message=str(exc)),
        request_id=request_id,
    ).to_dict()


def build_cors_headers(
    origins: Optional[str] = "*",
    methods: Optional[str] = "GET, POST, PUT, DELETE, OPTIONS",
    headers: Optional[str] = "Content-Type, Authorization, X-Request-Id",
) -> Dict[str, str]:
    return {
        "Access-Control-Allow-Origin": origins or "*",
        "Access-Control-Allow-Methods": methods or "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": headers or "Content-Type, Authorization, X-Request-Id",
    }
