from api.middleware import error_handler, generate_request_id, build_cors_headers
from api.errors import (
    NotFoundError, ValidationError, APIException, BadRequestError, ConflictError, RateLimitError,
)


class TestErrorHandler:

    def test_api_exception(self):
        exc = NotFoundError(message="test not found")
        result = error_handler(None, exc, request_id="req123")
        assert result["success"] is False
        assert result["error"]["code"] == "NOT_FOUND"
        assert result["error"]["message"] == "test not found"
        assert result["request_id"] == "req123"

    def test_generic_exception(self):
        exc = ValueError("something broke")
        result = error_handler(None, exc)
        assert result["success"] is False
        assert result["error"]["code"] == "UNEXPECTED_ERROR"

    def test_validation_error(self):
        exc = ValidationError(message="invalid input", details={"field": "score"})
        result = error_handler(None, exc)
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["error"]["details"]["field"] == "score"


class TestGenerateRequestId:

    def test_generates_string(self):
        rid = generate_request_id()
        assert isinstance(rid, str)
        assert len(rid) == 12


class TestBuildCorsHeaders:

    def test_defaults(self):
        headers = build_cors_headers()
        assert headers["Access-Control-Allow-Origin"] == "*"

    def test_custom(self):
        headers = build_cors_headers(origins="https://example.com")
        assert headers["Access-Control-Allow-Origin"] == "https://example.com"
