from api.schemas import (
    APIResponse, APIError, PaginatedResponse,
    HealthStatus, MetricsResponse, DecisionResponse, IntelligenceResponse,
    SortParam, build_paginated_response, set_api_metadata, get_api_metadata,
)


class TestAPIResponse:

    def test_defaults(self):
        resp = APIResponse()
        d = resp.to_dict()
        assert d["success"] is True
        assert d["version"] == "1.0.0"
        assert "timestamp" in d
        assert "request_id" not in d

    def test_with_data(self):
        resp = APIResponse(data={"key": "value"})
        d = resp.to_dict()
        assert d["data"] == {"key": "value"}

    def test_with_error(self):
        err = APIError(code="TEST", message="test error")
        resp = APIResponse(success=False, error=err)
        d = resp.to_dict()
        assert d["success"] is False
        assert d["error"]["code"] == "TEST"

    def test_with_request_id(self):
        resp = APIResponse(request_id="abc123")
        d = resp.to_dict()
        assert d["request_id"] == "abc123"


class TestAPIError:

    def test_to_dict(self):
        err = APIError(code="NOT_FOUND", message="not found", details={"id": 1})
        d = err.to_dict()
        assert d["code"] == "NOT_FOUND"
        assert d["details"]["id"] == 1

    def test_to_dict_no_details(self):
        err = APIError(code="ERR", message="msg")
        d = err.to_dict()
        assert "details" not in d


class TestPaginatedResponse:

    def test_to_dict(self):
        p = PaginatedResponse(items=[1, 2], total=10, page=1, page_size=2, total_pages=5)
        d = p.to_dict()
        assert d["total"] == 10
        assert d["total_pages"] == 5
        assert len(d["items"]) == 2

    def test_navigation_fields(self):
        p = PaginatedResponse(items=[], total=25, page=1, page_size=10, total_pages=3)
        d = p.to_dict()
        assert d["has_next"] is True
        assert d["has_prev"] is False
        assert d["next_page"] == 2
        assert d["prev_page"] is None

    def test_last_page(self):
        p = PaginatedResponse(items=[], total=25, page=3, page_size=10, total_pages=3)
        d = p.to_dict()
        assert d["has_next"] is False
        assert d["has_prev"] is True
        assert d["next_page"] is None
        assert d["prev_page"] == 2


class TestBuildPaginatedResponse:

    def test_build(self):
        p = build_paginated_response(items=["a", "b"], total=20, page=1, page_size=2)
        assert p.total == 20
        assert p.total_pages == 10
        assert p.has_next is True
        assert p.has_prev is False

    def test_empty(self):
        p = build_paginated_response(items=[], total=0, page=1, page_size=10)
        assert p.total_pages == 1
        assert p.items == []


class TestSortParam:

    def test_defaults(self):
        s = SortParam()
        d = s.to_dict()
        assert d["field"] == "timestamp"
        assert d["order"] == "desc"

    def test_custom(self):
        s = SortParam(field="score", order="asc")
        d = s.to_dict()
        assert d["field"] == "score"
        assert d["order"] == "asc"


class TestApiMetadata:

    def test_set_get(self):
        set_api_metadata(name="test", version="2.0")
        meta = get_api_metadata()
        assert meta["name"] == "test"
        assert meta["version"] == "2.0"

    def test_default(self):
        meta = get_api_metadata()
        assert isinstance(meta, dict)


class TestHealthStatus:

    def test_to_dict(self):
        h = HealthStatus(status="healthy", modules={"whale": True}, database="connected", uptime_seconds=100.0)
        d = h.to_dict()
        assert d["status"] == "healthy"
        assert d["database"] == "connected"


class TestMetricsResponse:

    def test_to_dict(self):
        m = MetricsResponse(evaluate_calls=10, modules_active=3)
        d = m.to_dict()
        assert d["evaluate_calls"] == 10
        assert d["modules_active"] == 3


class TestDecisionResponse:

    def test_to_dict(self):
        dr = DecisionResponse(
            signal_id=1, decision="APPROVED", score=85.0,
            confidence=80.0, confidence_label="STRONG_APPROVE",
            reasons={"approval": ["ok"], "rejection": []},
            timestamp="2024-01-01T00:00:00",
        )
        d = dr.to_dict()
        assert d["signal_id"] == 1
        assert d["confidence_label"] == "STRONG_APPROVE"


class TestIntelligenceResponse:

    def test_to_dict(self):
        ir = IntelligenceResponse(
            unified_score=75.0,
            module_scores={"whale": 80.0},
            health={"whale": True},
            report={"breakdown": {}},
        )
        d = ir.to_dict()
        assert d["unified_score"] == 75.0
