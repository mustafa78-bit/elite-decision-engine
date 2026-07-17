import pytest
from core.health import HealthChecker, check_secrets, validate_startup_config


class TestHealthChecker:

    def test_check_returns_health_status(self):
        hc = HealthChecker()
        status = hc.check()
        assert status.status in ("healthy", "degraded", "unhealthy")
        assert hasattr(status, "modules")
        assert hasattr(status, "database")
        assert hasattr(status, "uptime_seconds")
        assert hasattr(status, "version")
        assert hasattr(status, "timestamp")

    def test_check_to_dict(self):
        hc = HealthChecker()
        d = hc.check().to_dict()
        assert isinstance(d, dict)
        assert "status" in d
        assert "modules" in d
        assert "database" in d

    def test_is_ready_default(self):
        hc = HealthChecker()
        assert hc.is_ready() is True

    def test_is_alive_default(self):
        hc = HealthChecker()
        assert hc.is_alive() is True

    def test_get_metrics_returns_dict(self):
        hc = HealthChecker()
        metrics = hc.get_metrics()
        d = metrics.to_dict()
        assert "evaluate_calls" in d
        assert "modules_active" in d
        assert "uptime_seconds" in d

    def test_get_extended_metrics(self):
        hc = HealthChecker()
        em = hc.get_extended_metrics()
        assert "evaluate_calls" in em
        assert "database_status" in em
        assert "secret_warnings_count" in em
        assert "config_warnings_count" in em
        assert "module_history" in em

    def test_start_stop(self):
        hc = HealthChecker()
        hc.start()
        hc.stop()

    def test_cache_stats_provider(self):
        hc = HealthChecker()
        stats = {"size": 42}
        hc.set_cache_stats_provider(lambda: stats)
        em = hc.get_extended_metrics()
        assert em.get("cache", {}).get("size") == 42

    def test_cache_stats_provider_error_handling(self):
        hc = HealthChecker()
        def broken():
            raise ValueError("fail")
        hc.set_cache_stats_provider(broken)
        em = hc.get_extended_metrics()
        assert em.get("cache", {}).get("size") == 0

    def test_get_db_status_default(self):
        hc = HealthChecker()
        assert hc.get_db_status() == "unknown"


class TestCheckSecrets:

    def test_check_secrets_returns_list(self):
        result = check_secrets()
        assert isinstance(result, list)


class TestValidateStartupConfig:

    def test_validate_startup_config_returns_list(self):
        result = validate_startup_config()
        assert isinstance(result, list)


class TestMetricsResponse:

    def test_to_dict(self):
        from core.health import MetricsResponse
        m = MetricsResponse(evaluate_calls=10, modules_active=3, decisions_made=5, signals_processed=5)
        d = m.to_dict()
        assert d["evaluate_calls"] == 10
        assert d["modules_active"] == 3
        assert d["decisions_made"] == 5
        assert d["signals_processed"] == 5
        assert d["uptime_seconds"] == 0
        assert d["memory_entries"] == 0


class TestHealthStatus:

    def test_to_dict(self):
        from core.health import HealthStatus
        h = HealthStatus(status="healthy", modules={"whale": True}, database="connected", uptime_seconds=100.0)
        d = h.to_dict()
        assert d["status"] == "healthy"
        assert d["modules"]["whale"] is True
        assert d["database"] == "connected"
        assert d["uptime_seconds"] == 100.0
        assert d["version"] == "1.0.0"
        assert "timestamp" in d
