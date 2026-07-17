from api.schemas import (
    APIResponse,
    APIError,
    PaginatedResponse,
    HealthStatus,
    MetricsResponse,
    DecisionResponse,
    IntelligenceResponse,
    SortParam,
    build_paginated_response,
    set_api_metadata,
    get_api_metadata,
)
from api.errors import (
    APIException,
    BadRequestError,
    NotFoundError,
    ConflictError,
    ValidationError,
    RateLimitError,
    ServiceUnavailableError,
)
from api.middleware import (
    RequestTimingMiddleware,
    error_handler,
    generate_request_id,
    build_cors_headers,
)



def APIApp(*args, **kwargs):
    import importlib
    mod = importlib.import_module("api.app")
    return mod.APIApp(*args, **kwargs)


def create_app(*args, **kwargs):
    import importlib
    mod = importlib.import_module("api.app")
    return mod.create_app(*args, **kwargs)

__all__ = [
    "APIResponse",
    "APIError",
    "PaginatedResponse",
    "HealthStatus",
    "MetricsResponse",
    "DecisionResponse",
    "IntelligenceResponse",
    "SortParam",
    "build_paginated_response",
    "set_api_metadata",
    "get_api_metadata",
    "APIException",
    "BadRequestError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "RateLimitError",
    "ServiceUnavailableError",
    "RequestTimingMiddleware",
    "error_handler",
    "generate_request_id",
    "build_cors_headers",
    "APIApp",
    "create_app",
]
