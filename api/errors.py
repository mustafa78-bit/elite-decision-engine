from typing import Any, Dict, Optional


_STATUS_CODES = {
    "BAD_REQUEST": 400,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "VALIDATION_ERROR": 422,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}


class APIException(Exception):

    def __init__(
        self,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
        message: str = "An internal error occurred",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(self.message)


class BadRequestError(APIException):
    def __init__(self, message: str = "Bad request", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=400, code="BAD_REQUEST", message=message, details=details)


class NotFoundError(APIException):
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=404, code="NOT_FOUND", message=message, details=details)


class ConflictError(APIException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=409, code="CONFLICT", message=message, details=details)


class ValidationError(APIException):
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=422, code="VALIDATION_ERROR", message=message, details=details)


class RateLimitError(APIException):
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=429, code="RATE_LIMITED", message=message, details=details)


class ServiceUnavailableError(APIException):
    def __init__(self, message: str = "Service unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=503, code="SERVICE_UNAVAILABLE", message=message, details=details)
