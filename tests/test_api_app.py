from api.app import create_app, APIApp
from core.engine import DecisionEngine


class TestAPIApp:

    def test_create_app(self):
        app = create_app()
        assert isinstance(app, APIApp)
        assert app.engine is not None
        assert app.health is not None
        assert app.ws_manager is not None
        assert app.router is not None

    def test_startup_shutdown(self):
        app = create_app()
        app.startup()
        assert app._startup_time is not None
        app.shutdown()

    def test_uptime_seconds(self):
        app = create_app()
        assert app.uptime_seconds == 0.0
        app.startup()
        assert app.uptime_seconds >= 0.0
        app.shutdown()

    def test_create_app_with_engine(self):
        engine = DecisionEngine()
        app = create_app(engine=engine)
        assert app.engine is engine

    def test_get_app_info(self):
        app = create_app()
        info = app.get_app_info()
        assert info["name"] == "Elite Decision Engine API"
        assert info["version"] == "1.0.0"
        assert "uptime_seconds" in info
        assert "healthy" in info

    def test_get_openapi_spec(self):
        app = create_app()
        spec = app.get_openapi_spec()
        assert spec["openapi"] == "3.0.3"
        assert spec["info"]["title"] == "Elite Decision Engine API"
        assert "/health" in spec["paths"]
        assert "/decisions" in spec["paths"]
        assert len(spec["paths"]["/decisions"]["get"]["parameters"]) >= 5

    def test_metadata_set(self):
        from api.schemas import get_api_metadata
        meta = get_api_metadata()
        assert meta["name"] == "Elite Decision Engine API"
