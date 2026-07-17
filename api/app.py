import logging
import time
from typing import Any, Dict, List, Optional

from core.engine import DecisionEngine
from core.health import HealthChecker
from api.routes import DecisionRouter
from api.websocket import WSManager
from api.schemas import APIResponse, set_api_metadata
from services.portfolio_service import PortfolioService
from services.intelligence_service import IntelligenceService
from services.notification_service import NotificationService
from services.real_time import UnifiedBroadcaster
from services.dashboard_api import DashboardAPI


class APIApp:

    def __init__(self, engine: Optional[DecisionEngine] = None):
        self.engine = engine or DecisionEngine()
        self.health = HealthChecker(engine=self.engine)
        self.ws_manager = WSManager()
        self.portfolio_service = PortfolioService()
        self.intelligence_service = IntelligenceService(engine=self.engine)
        self.notification_service = NotificationService()
        self.broadcaster = UnifiedBroadcaster(ws_manager=self.ws_manager)
        self.dashboard_api = DashboardAPI(
            engine=self.engine,
            health=self.health,
            portfolio_service=self.portfolio_service,
            intelligence_service=self.intelligence_service,
            notification_service=self.notification_service,
        )
        self.health.set_cache_stats_provider(self._get_cache_stats)
        self.router = DecisionRouter(
            engine=self.engine,
            health=self.health,
            portfolio_service=self.portfolio_service,
            intelligence_service=self.intelligence_service,
            notification_service=self.notification_service,
            broadcaster=self.broadcaster,
            dashboard_api=self.dashboard_api,
        )
        self._startup_time: Optional[float] = None
        self._app_metadata: Dict[str, Any] = {
            "name": "Elite Decision Engine API",
            "version": "1.0.0",
            "description": "Multi-module intelligence engine for crypto trading signal evaluation",
            "api_version": "1.0.0",
            "docs_url": "/docs",
            "openapi_url": "/openapi.json",
        }
        set_api_metadata(**self._app_metadata)

    def _get_cache_stats(self) -> Dict[str, Any]:
        caches = {}
        try:
            if hasattr(self.broadcaster, "_event_throttle") and hasattr(self.broadcaster._event_throttle, "get_stats"):
                caches["throttle"] = self.broadcaster._event_throttle.get_stats()
        except Exception:
            caches["throttle"] = {"size": 0}
        caches["diagnostics"] = {"dashboard_api": self.dashboard_api.get_diagnostics() if hasattr(self.dashboard_api, "get_diagnostics") else {}}
        return caches

    def startup(self) -> None:
        self._startup_time = time.time()
        self.health.start()
        self.engine.intelligence.evaluate()
        if hasattr(self.broadcaster, "start") and callable(self.broadcaster.start):
            self.broadcaster.start()
        logger = logging.getLogger(__name__)
        logger.info("APIApp startup complete")

    def shutdown(self) -> None:
        self.health.stop()
        if hasattr(self.broadcaster, "stop") and callable(self.broadcaster.stop):
            self.broadcaster.stop()
        logger = logging.getLogger(__name__)
        logger.info("APIApp shutdown complete")

    @property
    def uptime_seconds(self) -> float:
        if self._startup_time is None:
            return 0.0
        return time.time() - self._startup_time

    def get_app_info(self) -> Dict[str, Any]:
        return {
            **self._app_metadata,
            "uptime_seconds": self.uptime_seconds,
            "healthy": self.health.is_alive(),
        }

    def _build_path(self, summary: str, description: str, method: str = "get", parameters: Optional[List[Dict]] = None) -> Dict:
        entry: Dict = {"summary": summary}
        if description:
            entry["description"] = description
        if parameters:
            entry["parameters"] = parameters
        entry["responses"] = {"200": {"description": "Success"}}
        return {method: entry}

    def get_openapi_spec(self) -> Dict[str, Any]:
        paths: Dict[str, Any] = {}
        p = self._build_path

        paths["/health"] = p("Health check", "Returns current system health status including module health")
        paths["/ready"] = p("Readiness probe", "Returns whether the system is ready to accept requests")
        paths["/live"] = p("Liveness probe", "Returns whether the system is alive")
        paths["/metrics"] = p("Runtime metrics", "Returns runtime metrics including evaluate calls, decisions made")
        paths["/metrics/extended"] = p("Extended metrics", "Returns extended metrics including diagnostics, cache stats, broadcaster info")

        decisions_params = [
            {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
            {"name": "page_size", "in": "query", "schema": {"type": "integer", "default": 10}},
            {"name": "decision", "in": "query", "schema": {"type": "string", "enum": ["APPROVED", "REJECTED"]}},
            {"name": "sort_by", "in": "query", "schema": {"type": "string", "enum": ["score", "confidence", "timestamp", "signal_id", "decision"]}},
            {"name": "sort_order", "in": "query", "schema": {"type": "string", "enum": ["asc", "desc"]}},
            {"name": "score_min", "in": "query", "schema": {"type": "number"}},
            {"name": "score_max", "in": "query", "schema": {"type": "number"}},
            {"name": "status", "in": "query", "schema": {"type": "string"}},
            {"name": "date_from", "in": "query", "schema": {"type": "string"}},
            {"name": "date_to", "in": "query", "schema": {"type": "string"}},
        ]
        paths["/decisions"] = p("Decision history", "Returns paginated decision history with filtering and sorting", parameters=decisions_params)
        paths["/decisions/{signal_id}"] = p("Decision by ID", "Returns a single decision by signal ID")
        paths["/intelligence"] = p("Intelligence overview", "Returns current intelligence evaluation results")
        paths["/intelligence/detail"] = p("Intelligence detail", "Returns detailed intelligence breakdown")
        paths["/features"] = p("All features", "Returns all module features")
        paths["/modules"] = p("Module diagnostics", "Returns module diagnostics and health")
        paths["/portfolio"] = p("Portfolio detail", "Returns full portfolio details with equity curve")
        paths["/portfolio/summary"] = p("Portfolio summary", "Returns portfolio summary stats")
        paths["/portfolio/equity-curve"] = p("Equity curve", "Returns portfolio equity curve points", parameters=[{"name": "limit", "in": "query", "schema": {"type": "integer", "default": 100}}])
        paths["/notifications"] = {
            "get": {
                "summary": "List notifications",
                "description": "Returns notification history with optional filters",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 50}},
                    {"name": "category", "in": "query", "schema": {"type": "string"}},
                    {"name": "severity", "in": "query", "schema": {"type": "string"}},
                    {"name": "unread_only", "in": "query", "schema": {"type": "boolean", "default": False}},
                    {"name": "min_priority", "in": "query", "schema": {"type": "integer"}},
                ],
                "responses": {"200": {"description": "Notifications list"}},
            },
            "post": {
                "summary": "Create notification",
                "description": "Creates a new notification",
                "responses": {"200": {"description": "Created notification"}},
            },
        }
        paths["/notifications/{id}/read"] = p("Mark notification read", "Marks a single notification as read", method="post")
        paths["/notifications/read-all"] = p("Mark all read", "Marks all notifications as read", method="post")
        paths["/notifications/alerts/summary"] = p("Alert summary", "Returns alert summary statistics")
        paths["/notifications/categories"] = p("Notification categories", "Returns available notification categories")
        paths["/dashboard/overview"] = p("Dashboard overview", "Returns aggregated dashboard overview", parameters=[{"name": "force_refresh", "in": "query", "schema": {"type": "boolean", "default": False}}])
        paths["/dashboard/widgets"] = p("Dashboard widgets", "Returns dashboard widget data")
        paths["/dashboard/kpis"] = p("Dashboard KPIs", "Returns dashboard KPI data")
        paths["/dashboard/intelligence"] = p("Dashboard intelligence", "Returns intelligence section of dashboard")
        paths["/dashboard/market"] = p("Dashboard market", "Returns market overview section")
        paths["/dashboard/risk"] = p("Dashboard risk", "Returns risk overview section")
        paths["/dashboard/portfolio"] = p("Dashboard portfolio", "Returns portfolio overview section")
        paths["/dashboard/notifications"] = p("Dashboard notifications", "Returns notification overview section")
        paths["/dashboard/monitoring"] = p("Dashboard monitoring", "Returns monitoring overview section")
        paths["/dashboard/performance"] = p("Dashboard performance", "Returns performance overview section")
        paths["/dashboard/diagnostics"] = p("Dashboard diagnostics", "Returns dashboard API diagnostics")
        paths["/dashboard/metrics"] = p("Dashboard metrics", "Returns dashboard cache and call metrics")
        paths["/preferences"] = {
            "get": {
                "summary": "Get preferences",
                "description": "Returns user preferences",
                "parameters": [{"name": "user_id", "in": "query", "schema": {"type": "string"}}],
                "responses": {"200": {"description": "User preferences"}},
            },
            "put": {
                "summary": "Update preferences",
                "description": "Updates user preferences",
                "responses": {"200": {"description": "Updated preferences"}},
            },
        }
        paths["/preferences/theme"] = p("Set theme", "Sets the UI theme for a user", method="post", parameters=[{"name": "theme", "in": "query", "schema": {"type": "string"}}])
        paths["/preferences/language"] = p("Set language", "Sets the UI language for a user", method="post", parameters=[{"name": "language", "in": "query", "schema": {"type": "string"}}])
        paths["/layouts"] = {
            "get": {
                "summary": "Get layouts",
                "description": "Returns saved layouts for a user",
                "parameters": [{"name": "user_id", "in": "query", "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Layouts list"}},
            },
            "post": {
                "summary": "Save layout",
                "description": "Saves a new layout for a user",
                "responses": {"200": {"description": "Saved layout"}},
            },
        }
        paths["/layouts/{layout_id}"] = p("Delete layout", "Deletes a saved layout", method="delete")
        paths["/presets"] = p("Get presets", "Returns available presets")
        paths["/presets/{preset_id}/apply"] = p("Apply preset", "Applies a preset for a user", method="post")
        paths["/favorites"] = {
            "get": {
                "summary": "Get favorites",
                "description": "Returns favorite symbols for a user",
                "parameters": [{"name": "user_id", "in": "query", "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Favorites list"}},
            },
            "post": {
                "summary": "Add favorite",
                "description": "Adds a symbol to user favorites",
                "responses": {"200": {"description": "Updated favorites"}},
            },
        }
        paths["/favorites/{symbol}"] = p("Remove favorite", "Removes a symbol from user favorites", method="delete")
        paths["/watchlist"] = {
            "get": {
                "summary": "Get watchlist",
                "description": "Returns watchlist symbols for a user",
                "parameters": [{"name": "user_id", "in": "query", "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Watchlist list"}},
            },
            "post": {
                "summary": "Add to watchlist",
                "description": "Adds a symbol to user watchlist",
                "responses": {"200": {"description": "Updated watchlist"}},
            },
        }
        paths["/watchlist/{symbol}"] = p("Remove from watchlist", "Removes a symbol from user watchlist", method="delete")
        paths["/activity"] = p("Recent activity", "Returns recent user activity", parameters=[{"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}}])
        paths["/sessions"] = {
            "get": {
                "summary": "Get session",
                "description": "Returns current session for a user",
                "parameters": [{"name": "user_id", "in": "query", "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Session info"}},
            },
            "post": {
                "summary": "Create session",
                "description": "Creates a new session for a user",
                "responses": {"200": {"description": "Created session"}},
            },
        }

        return {
            "openapi": "3.0.3",
            "info": {
                "title": self._app_metadata["name"],
                "version": self._app_metadata["version"],
                "description": self._app_metadata["description"],
            },
            "paths": paths,
        }


def create_app(engine: Optional[DecisionEngine] = None) -> APIApp:
    return APIApp(engine=engine)
