from unittest.mock import MagicMock, patch

import monitoring.health as health_module
from monitoring.health import HealthService
from notifications.dispatcher import NotificationDispatcher
from notifications.events import TradeEvent


def _reset_health_state():
    health_module._INTERNAL_ERRORS.clear()
    health_module._LAST_KNOWN_STATUS.clear()


def _mock_checks(ok: bool | dict[str, bool]):
    """Patch database()/collector()/execution() to simulate ok/failing checks.

    `ok` can be a single bool applied to all 3 components, or a per-component dict
    (e.g. {"database": False, "collector": True, "execution": True}) to isolate a
    single component's transition.
    """
    per_component = ok if isinstance(ok, dict) else {
        "database": ok, "collector": ok, "execution": ok,
    }

    def _fake(component):
        component_ok = per_component[component]
        status = "ok" if component_ok else "error"

        def _run():
            health_module._track_result(component, component_ok, 1.0)
            return {"status": status, "detail": None if component_ok else "simulated failure"}
        return _run

    patches = [
        patch.object(HealthService, "database", staticmethod(_fake("database"))),
        patch.object(HealthService, "collector", staticmethod(_fake("collector"))),
        patch.object(HealthService, "execution", staticmethod(_fake("execution"))),
    ]
    for p in patches:
        p.start()
    return patches


def _stop(patches):
    for p in patches:
        p.stop()


class TestHealthCheckAndAlertTransitions:

    def setup_method(self):
        _reset_health_state()

    def teardown_method(self):
        _reset_health_state()

    def test_no_alert_on_first_tick(self):
        dispatcher = MagicMock()
        patches = _mock_checks(ok=True)
        try:
            HealthService.check_and_alert(dispatcher=dispatcher)
        finally:
            _stop(patches)

        dispatcher.emit.assert_not_called()

    def test_no_alert_while_healthy(self):
        dispatcher = MagicMock()
        patches = _mock_checks(ok=True)
        try:
            for _ in range(5):
                HealthService.check_and_alert(dispatcher=dispatcher)
        finally:
            _stop(patches)

        dispatcher.emit.assert_not_called()

    def test_no_alert_below_failure_threshold(self):
        dispatcher = MagicMock()
        ok_patches = _mock_checks(ok=True)
        HealthService.check_and_alert(dispatcher=dispatcher)  # establish healthy baseline
        _stop(ok_patches)

        db_down = {"database": False, "collector": True, "execution": True}
        fail_patches = _mock_checks(db_down)
        try:
            # 2 consecutive failures, threshold is 3 — should not alert yet
            HealthService.check_and_alert(dispatcher=dispatcher, failure_threshold=3)
            HealthService.check_and_alert(dispatcher=dispatcher, failure_threshold=3)
        finally:
            _stop(fail_patches)

        dispatcher.emit.assert_not_called()

    def test_alert_fires_once_on_degraded_then_once_on_recovery(self):
        # Only "database" transitions — "collector"/"execution" stay healthy
        # throughout, so we can assert exact emit call counts for one component.
        dispatcher = MagicMock()

        ok_patches = _mock_checks(ok=True)
        HealthService.check_and_alert(dispatcher=dispatcher)  # baseline, no alert
        _stop(ok_patches)

        db_down = {"database": False, "collector": True, "execution": True}
        fail_patches = _mock_checks(db_down)
        try:
            # 3 consecutive failures crosses the threshold on the 3rd tick
            HealthService.check_and_alert(dispatcher=dispatcher, failure_threshold=3)
            HealthService.check_and_alert(dispatcher=dispatcher, failure_threshold=3)
            HealthService.check_and_alert(dispatcher=dispatcher, failure_threshold=3)
            # staying unhealthy for more ticks must NOT emit again
            HealthService.check_and_alert(dispatcher=dispatcher, failure_threshold=3)
            HealthService.check_and_alert(dispatcher=dispatcher, failure_threshold=3)
        finally:
            _stop(fail_patches)

        assert dispatcher.emit.call_count == 1
        degraded_event, degraded_payload = dispatcher.emit.call_args[0]
        assert degraded_event == TradeEvent.SYSTEM_HEALTH_DEGRADED
        assert degraded_payload["component"] == "database"

        recover_patches = _mock_checks(ok=True)
        try:
            HealthService.check_and_alert(dispatcher=dispatcher, failure_threshold=3)
            HealthService.check_and_alert(dispatcher=dispatcher, failure_threshold=3)
        finally:
            _stop(recover_patches)

        assert dispatcher.emit.call_count == 2
        recovered_event, recovered_payload = dispatcher.emit.call_args[0]
        assert recovered_event == TradeEvent.SYSTEM_HEALTH_RECOVERED
        assert recovered_payload["component"] == "database"

    def test_check_and_alert_returns_checks_without_dispatcher(self):
        patches = _mock_checks(ok=True)
        try:
            result = HealthService.check_and_alert(dispatcher=None)
        finally:
            _stop(patches)

        assert set(result.keys()) == {"database", "collector", "execution"}


class TestSystemHealthTelegramAlerts:

    def test_dispatcher_proactive_telegram_health_degraded(self):
        mock_bot = MagicMock()
        mock_bot.send_alert_threadsafe = MagicMock()

        dispatcher = NotificationDispatcher(telegram_bot_manager=mock_bot)

        payload = {
            "component": "database",
            "status": "error",
            "detail": "connection refused",
            "consecutive_failures": 3,
        }
        result = dispatcher.emit(TradeEvent.SYSTEM_HEALTH_DEGRADED, payload)

        assert result["event"] == "SYSTEM_HEALTH_DEGRADED"
        mock_bot.send_alert_threadsafe.assert_called_once()
        alert_text = mock_bot.send_alert_threadsafe.call_args[0][0]
        assert "SYSTEM HEALTH DEGRADED" in alert_text
        assert "database" in alert_text
        assert "connection refused" in alert_text

    def test_dispatcher_proactive_telegram_health_recovered(self):
        mock_bot = MagicMock()
        mock_bot.send_alert_threadsafe = MagicMock()

        dispatcher = NotificationDispatcher(telegram_bot_manager=mock_bot)

        payload = {"component": "collector", "status": "ok"}
        result = dispatcher.emit(TradeEvent.SYSTEM_HEALTH_RECOVERED, payload)

        assert result["event"] == "SYSTEM_HEALTH_RECOVERED"
        mock_bot.send_alert_threadsafe.assert_called_once()
        alert_text = mock_bot.send_alert_threadsafe.call_args[0][0]
        assert "SYSTEM HEALTH RECOVERED" in alert_text
        assert "collector" in alert_text
