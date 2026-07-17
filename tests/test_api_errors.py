from api.errors import (
    APIException, BadRequestError, NotFoundError, ConflictError,
    ValidationError, RateLimitError, ServiceUnavailableError,
)


class TestAPIException:

    def test_defaults(self):
        exc = APIException()
        assert exc.status_code == 500
        assert exc.code == "INTERNAL_ERROR"
        assert str(exc) == "An internal error occurred"

    def test_custom(self):
        exc = APIException(status_code=400, code="BAD_REQUEST", message="bad")
        assert exc.status_code == 400
        assert exc.code == "BAD_REQUEST"


class TestBadRequestError:

    def test_defaults(self):
        exc = BadRequestError()
        assert exc.status_code == 400
        assert exc.code == "BAD_REQUEST"

    def test_custom_message(self):
        exc = BadRequestError(message="Invalid param")
        assert str(exc) == "Invalid param"


class TestNotFoundError:

    def test_defaults(self):
        exc = NotFoundError()
        assert exc.status_code == 404
        assert exc.code == "NOT_FOUND"

    def test_custom_message(self):
        exc = NotFoundError(message="Signal not found")
        assert str(exc) == "Signal not found"


class TestConflictError:

    def test_defaults(self):
        exc = ConflictError()
        assert exc.status_code == 409
        assert exc.code == "CONFLICT"


class TestValidationError:

    def test_defaults(self):
        exc = ValidationError()
        assert exc.status_code == 422
        assert exc.code == "VALIDATION_ERROR"


class TestRateLimitError:

    def test_defaults(self):
        exc = RateLimitError()
        assert exc.status_code == 429
        assert exc.code == "RATE_LIMITED"


class TestServiceUnavailableError:

    def test_defaults(self):
        exc = ServiceUnavailableError()
        assert exc.status_code == 503
        assert exc.code == "SERVICE_UNAVAILABLE"
