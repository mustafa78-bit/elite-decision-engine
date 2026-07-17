from api.websocket import WSManager, WSEvent, WSEventType, WSNotificationPayload, WSDashboardPayload


class TestWSEvent:

    def test_defaults(self):
        event = WSEvent(event_type=WSEventType.DECISION, data={"key": "value"})
        d = event.to_dict()
        assert d["event_type"] == "decision"
        assert d["data"]["key"] == "value"
        assert d["version"] == "2.0"
        assert "event_id" in d

    def test_all_types(self):
        for t in WSEventType:
            event = WSEvent(event_type=t, data={})
            assert event.to_dict()["event_type"] == t.value

    def test_notification_type(self):
        assert WSEventType.NOTIFICATION.value == "notification"

    def test_dashboard_type(self):
        assert WSEventType.DASHBOARD.value == "dashboard"


class TestWSNotificationPayload:

    def test_to_dict(self):
        p = WSNotificationPayload(type="warning", title="Test", message="msg", severity="high")
        d = p.to_dict()
        assert d["type"] == "warning"
        assert d["severity"] == "high"

    def test_defaults(self):
        p = WSNotificationPayload()
        assert p.type == "info"


class TestWSDashboardPayload:

    def test_to_dict(self):
        p = WSDashboardPayload(portfolio={"trades": 5}, intelligence={"score": 80.0})
        d = p.to_dict()
        assert d["portfolio"]["trades"] == 5
        assert d["intelligence"]["score"] == 80.0

    def test_defaults(self):
        p = WSDashboardPayload()
        assert p.portfolio == {}
        assert p.intelligence == {}


class TestWSManager:

    def test_initial_state(self):
        mgr = WSManager()
        assert mgr.active_connections == 0

    def test_register_unregister(self):
        mgr = WSManager()

        class MockConn:
            async def send_json(self, data):
                pass

        conn = MockConn()
        import asyncio
        asyncio.run(mgr.register(conn))
        assert mgr.active_connections == 1
        asyncio.run(mgr.unregister(conn))
        assert mgr.active_connections == 0

    def test_max_connections(self):
        mgr = WSManager()
        mgr._max_connections = 2

        class MockConn:
            async def send_json(self, data):
                pass
            def __eq__(self, other):
                return id(self) == id(other)
            def __hash__(self):
                return id(self)

        import asyncio
        conns = [MockConn() for _ in range(5)]
        for c in conns:
            asyncio.run(mgr.register(c))
        assert mgr.active_connections == 2

    def test_get_connection_info(self):
        mgr = WSManager()
        info = mgr.get_connection_info()
        assert info["active_connections"] == 0
        assert info["max_connections"] == 1000
        assert isinstance(info["connections"], list)
