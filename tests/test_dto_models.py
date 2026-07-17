from dto.models import (
    DashboardDTO, PortfolioDTO, TradeDTO, IntelligenceDTO,
    RiskDTO, MonitoringDTO, NotificationDTO, WebSocketDTO,
)


class TestPortfolioDTO:

    def test_to_dict(self):
        p = PortfolioDTO(total_trades=10, win_rate=60.0, total_pnl=5000.0)
        d = p.to_dict()
        assert d["total_trades"] == 10
        assert d["win_rate"] == 60.0

    def test_defaults(self):
        p = PortfolioDTO()
        assert p.total_trades == 0


class TestTradeDTO:

    def test_to_dict(self):
        t = TradeDTO(id=1, symbol="BTC", side="LONG", entry_price=50000, status="OPEN")
        d = t.to_dict()
        assert d["symbol"] == "BTC"
        assert d["status"] == "OPEN"


class TestIntelligenceDTO:

    def test_to_dict(self):
        i = IntelligenceDTO(unified_score=75.0, whale_health=True)
        d = i.to_dict()
        assert d["unified_score"] == 75.0
        assert d["whale_health"] is True

    def test_defaults(self):
        i = IntelligenceDTO()
        assert i.unified_score == 50.0


class TestRiskDTO:

    def test_to_dict(self):
        r = RiskDTO(risk_score=25.0, max_drawdown=10.0)
        d = r.to_dict()
        assert d["risk_score"] == 25.0


class TestMonitoringDTO:

    def test_to_dict(self):
        m = MonitoringDTO(evaluate_calls=100, modules_active=7, uptime_hours=24.0)
        d = m.to_dict()
        assert d["evaluate_calls"] == 100


class TestNotificationDTO:

    def test_to_dict(self):
        n = NotificationDTO(type="warning", title="Test", message="test msg", severity="medium")
        d = n.to_dict()
        assert d["type"] == "warning"
        assert d["severity"] == "medium"


class TestWebSocketDTO:

    def test_to_dict(self):
        w = WebSocketDTO(event="decision", data={"id": 1})
        d = w.to_dict()
        assert d["event"] == "decision"
        assert d["data"]["id"] == 1


class TestDashboardDTO:

    def test_to_dict(self):
        dto = DashboardDTO(
            portfolio=PortfolioDTO(total_trades=5),
            intelligence=IntelligenceDTO(unified_score=80.0),
        )
        d = dto.to_dict()
        assert d["portfolio"]["total_trades"] == 5
        assert d["intelligence"]["unified_score"] == 80.0
        assert "recent_decisions" in d
        assert "recent_notifications" in d

    def test_notifications_capped(self):
        from dto.models import NotificationDTO
        dto = DashboardDTO()
        for i in range(30):
            dto.recent_notifications.append(NotificationDTO(title=f"n{i}"))
        d = dto.to_dict()
        assert len(d["recent_notifications"]) == 20
