from unittest.mock import MagicMock, patch

import pytest
from api.routes import DecisionRouter
from api.errors import NotFoundError, BadRequestError
from core.engine import DecisionEngine
from core.health import HealthChecker


class TestDecisionRouter:

    def _make_router(self):
        engine = DecisionEngine()
        health = HealthChecker(engine=engine)
        return DecisionRouter(engine=engine, health=health)

    def test_get_health(self):
        router = self._make_router()
        result = router.get_health()
        assert result["success"] is True
        assert "data" in result

    def test_get_readiness(self):
        router = self._make_router()
        result = router.get_readiness()
        assert result["success"] is True
        assert "ready" in result["data"]

    def test_get_liveness(self):
        router = self._make_router()
        result = router.get_liveness()
        assert result["success"] is True
        assert "alive" in result["data"]

    def test_get_metrics(self):
        router = self._make_router()
        result = router.get_metrics()
        assert result["success"] is True

    def test_get_decisions_empty(self):
        router = self._make_router()
        result = router.get_decisions()
        assert result["success"] is True
        assert result["data"]["total"] == 0

    def test_get_decisions_pagination(self):
        router = self._make_router()
        result = router.get_decisions(page=1, page_size=5)
        assert result["success"] is True
        assert result["data"]["page_size"] == 5

    def test_get_decisions_invalid_page(self):
        router = self._make_router()
        with pytest.raises(BadRequestError):
            router.get_decisions(page=0)

    def test_get_decisions_invalid_page_size(self):
        router = self._make_router()
        with pytest.raises(BadRequestError):
            router.get_decisions(page_size=0)
        with pytest.raises(BadRequestError):
            router.get_decisions(page_size=200)

    def test_get_decisions_invalid_sort_field(self):
        router = self._make_router()
        with pytest.raises(BadRequestError):
            router.get_decisions(sort_by="invalid_field")

    def test_get_decisions_invalid_sort_order(self):
        router = self._make_router()
        with pytest.raises(BadRequestError):
            router.get_decisions(sort_order="invalid")

    def test_get_decisions_valid_sort(self):
        router = self._make_router()
        result = router.get_decisions(sort_by="score", sort_order="asc")
        assert result["success"] is True

    def test_get_decisions_filter_by_decision_invalid(self):
        router = self._make_router()
        with pytest.raises(BadRequestError):
            router.get_decisions(decision="INVALID")

    def test_get_decisions_navigation_fields(self):
        router = self._make_router()
        result = router.get_decisions(page=1, page_size=10)
        paginated = result["data"]
        assert "has_next" in paginated
        assert "has_prev" in paginated
        assert "next_page" in paginated
        assert "prev_page" in paginated

    def test_get_intelligence(self):
        router = self._make_router()
        result = router.get_intelligence()
        assert result["success"] is True
        assert "unified_score" in result["data"]

    def test_get_features(self):
        router = self._make_router()
        result = router.get_features()
        assert result["success"] is True

    def test_get_modules(self):
        router = self._make_router()
        result = router.get_modules()
        assert result["success"] is True

    def test_get_decision_by_id_not_found(self):
        router = self._make_router()
        with pytest.raises(NotFoundError):
            router.get_decision_by_id(signal_id=999)
