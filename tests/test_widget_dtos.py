from __future__ import annotations

from dto.widgets import (
    DashboardWidgetDTO,
    ExplanationDashboardWidgetDTO,
    KPIDashboardWidgetDTO,
    MonitoringDashboardWidgetDTO,
    NotificationDashboardWidgetDTO,
    PortfolioDashboardWidgetDTO,
    TimelineDashboardWidgetDTO,
)


class TestWidgetDTOs:

    def test_dashboard_widget_to_dict(self):
        dto = DashboardWidgetDTO(widget_id="test", widget_type="kpi", title="Test Widget", data={"value": 42})
        d = dto.to_dict()
        assert d["widget_id"] == "test"
        assert d["data"]["value"] == 42

    def test_kpi_widget_to_dict(self):
        dto = KPIDashboardWidgetDTO(kpis=[{"name": "PnL", "value": 5000}], period="24h")
        d = dto.to_dict()
        assert len(d["kpis"]) == 1
        assert d["period"] == "24h"

    def test_explanation_widget_to_dict(self):
        dto = ExplanationDashboardWidgetDTO(
            signal_id=1, decision="APPROVE", confidence=85.0,
            breakdown={"trend": 0.8, "volume": 0.6}, human_readable="Test explanation",
        )
        d = dto.to_dict()
        assert d["signal_id"] == 1
        assert d["decision"] == "APPROVE"

    def test_timeline_widget_to_dict(self):
        dto = TimelineDashboardWidgetDTO(
            events=[{"event": "start", "timestamp": "2024-01-01T00:00:00"}],
            total_duration_ms=150.5,
        )
        d = dto.to_dict()
        assert len(d["events"]) == 1
        assert d["total_duration_ms"] == 150.5

    def test_portfolio_widget_to_dict(self):
        dto = PortfolioDashboardWidgetDTO(
            total_pnl=5000.0, total_trades=10, open_trades=2,
            win_rate=60.0, equity=15000.0, max_drawdown=1000.0,
        )
        d = dto.to_dict()
        assert d["total_pnl"] == 5000.0
        assert d["win_rate"] == 60.0

    def test_monitoring_widget_to_dict(self):
        dto = MonitoringDashboardWidgetDTO(
            status="healthy", uptime_seconds=3600.0, database_status="connected",
            collector_status="ok", websocket_clients=3,
        )
        d = dto.to_dict()
        assert d["status"] == "healthy"
        assert d["websocket_clients"] == 3

    def test_notification_widget_to_dict(self):
        dto = NotificationDashboardWidgetDTO(
            unread_count=5,
            recent=[{"id": 1, "event_type": "test", "payload": {}}],
        )
        d = dto.to_dict()
        assert d["unread_count"] == 5
        assert len(d["recent"]) == 1

    def test_explanation_widget_empty(self):
        dto = ExplanationDashboardWidgetDTO()
        d = dto.to_dict()
        assert d["signal_id"] == 0
