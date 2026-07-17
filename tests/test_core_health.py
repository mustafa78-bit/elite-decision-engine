from unittest.mock import MagicMock, patch

from core.health import HealthChecker, check_secrets, validate_startup_config


class TestCheckSecrets:

    def test_returns_list(self):
        result = check_secrets()
        assert isinstance(result, list)


class TestValidateStartupConfig:

    def test_returns_list(self):
        result = validate_startup_config()
        assert isinstance(result, list)


class TestHealthChecker:

    def test_start_stop(self):
        hc = HealthChecker()
        hc.start()
        hc.stop()

    def test_check_without_engine(self):
        hc = HealthChecker()
        hc.start()
        status = hc.check()
        assert status.status in ("healthy", "unhealthy")
        assert status.uptime_seconds >= 0

    def test_is_ready_without_engine(self):
        hc = HealthChecker()
        assert hc.is_ready() is True

    def test_is_alive(self):
        hc = HealthChecker()
        assert hc.is_alive() is True

    def test_get_metrics(self):
        hc = HealthChecker()
        hc.start()
        metrics = hc.get_metrics()
        assert metrics.evaluate_calls >= 0
        assert metrics.uptime_seconds >= 0

    def test_get_extended_metrics(self):
        hc = HealthChecker()
        hc.start()
        ext = hc.get_extended_metrics()
        assert "database_status" in ext
        assert "secret_warnings_count" in ext
        assert "config_warnings_count" in ext
        assert "module_history" in ext

    def test_get_db_status(self):
        hc = HealthChecker()
        assert isinstance(hc.get_db_status(), str)

    def test_set_cache_stats_provider(self):
        hc = HealthChecker()
        mock_provider = MagicMock()
        mock_provider.get_stats.return_value = {"size": 5}
        hc.set_cache_stats_provider(mock_provider)
        ext = hc.get_extended_metrics()
        assert ext["cache"]["size"] == 5
