import time
from typing import Any, Dict, List, Optional

from api.schemas import (
    APIResponse,
    PaginatedResponse,
    HealthStatus,
    MetricsResponse,
    DecisionResponse,
    IntelligenceResponse,
    build_paginated_response,
)
from api.errors import NotFoundError, ValidationError, BadRequestError
from core.engine import DecisionEngine
from core.health import HealthChecker
from services.portfolio_service import PortfolioService
from services.intelligence_service import IntelligenceService
from services.notification_service import NotificationService
from services.real_time import UnifiedBroadcaster
from services.dashboard_api import DashboardAPI
from services.user_service import UserService


_SORTABLE_FIELDS = {"score", "confidence", "timestamp", "signal_id", "decision"}
_VALID_SORT_ORDERS = {"asc", "desc"}
_VALID_DECISIONS = {"APPROVED", "REJECTED"}


def _validate_sort(sort_by: Optional[str], sort_order: Optional[str]) -> tuple:
    if sort_by is not None and sort_by not in _SORTABLE_FIELDS:
        raise BadRequestError(
            f"Invalid sort field '{sort_by}'. Allowed: {', '.join(sorted(_SORTABLE_FIELDS))}",
            details={"valid_fields": sorted(_SORTABLE_FIELDS)},
        )
    if sort_order is not None and sort_order.lower() not in _VALID_SORT_ORDERS:
        raise BadRequestError(
            f"Invalid sort order '{sort_order}'. Allowed: asc, desc",
            details={"valid_orders": list(_VALID_SORT_ORDERS)},
        )
    return sort_by or "timestamp", (sort_order or "desc").lower()


def _validate_pagination(page: int, page_size: int) -> None:
    if page < 1:
        raise BadRequestError("Page must be >= 1", details={"page": page})
    if page_size < 1 or page_size > 100:
        raise BadRequestError("Page size must be 1-100", details={"page_size": page_size})


def _apply_sort(
    items: List[Dict[str, Any]], sort_by: str, sort_order: str
) -> List[Dict[str, Any]]:
    reverse = sort_order == "desc"
    try:
        return sorted(items, key=lambda x: x.get(sort_by, ""), reverse=reverse)
    except Exception:
        return items


def _apply_filters(
    history: List[Dict[str, Any]],
    decision: Optional[str] = None,
    score_min: Optional[float] = None,
    score_max: Optional[float] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filtered = history
    if decision is not None:
        d = decision.upper()
        if d not in _VALID_DECISIONS:
            raise BadRequestError(
                f"Invalid decision filter '{decision}'. Allowed: {', '.join(_VALID_DECISIONS)}",
                details={"valid_decisions": list(_VALID_DECISIONS)},
            )
        filtered = [h for h in filtered if h.get("decision", "").upper() == d]
    if score_min is not None:
        filtered = [h for h in filtered if h.get("score", 0) >= score_min]
    if score_max is not None:
        filtered = [h for h in filtered if h.get("score", 0) <= score_max]
    if status is not None:
        filtered = [h for h in filtered if h.get("status", "").upper() == status.upper()]
    if date_from is not None:
        filtered = [h for h in filtered if h.get("timestamp", "") >= date_from]
    if date_to is not None:
        filtered = [h for h in filtered if h.get("timestamp", "") <= date_to]
    return filtered


def _build_decision_response(h: Dict[str, Any]) -> Dict[str, Any]:
    return DecisionResponse(
        signal_id=h["signal_id"],
        decision=h["decision"],
        score=h["score"],
        confidence=h.get("confidence", 0),
        confidence_label=h.get("confidence_label", "NEUTRAL"),
        reasons=h.get("explanation", {}).get("reasons", {"approval": [], "rejection": []}),
        timestamp=h.get("timestamp", ""),
    ).to_dict()


class DecisionRouter:

    def __init__(
        self,
        engine: DecisionEngine,
        health: HealthChecker,
        portfolio_service: Optional[PortfolioService] = None,
        intelligence_service: Optional[IntelligenceService] = None,
        notification_service: Optional[NotificationService] = None,
        broadcaster: Optional[UnifiedBroadcaster] = None,
        dashboard_api: Optional[DashboardAPI] = None,
    ):
        self._engine = engine
        self._health = health
        self._portfolio = portfolio_service or PortfolioService()
        self._intel = intelligence_service or IntelligenceService(engine=engine)
        self._notifications = notification_service or NotificationService()
        self._broadcaster = broadcaster
        self._dashboard_api = dashboard_api
        self._user_service = UserService()
        self._ws_manager = getattr(broadcaster, "_ws", None) if broadcaster else None

    def _require_user_id(self, user_id: Optional[str]) -> str:
        return user_id or "anonymous"

    def get_health(self) -> Dict[str, Any]:
        status = self._health.check()
        return APIResponse(data=status.to_dict()).to_dict()

    def get_readiness(self) -> Dict[str, Any]:
        ready = self._health.is_ready()
        return APIResponse(data={"ready": ready, "status": "ready" if ready else "not_ready"}).to_dict()

    def get_liveness(self) -> Dict[str, Any]:
        alive = self._health.is_alive()
        return APIResponse(data={"alive": alive, "status": "alive" if alive else "dead"}).to_dict()

    def get_metrics(self) -> Dict[str, Any]:
        metrics = self._health.get_metrics()
        return APIResponse(data=metrics.to_dict()).to_dict()

    def get_extended_metrics(self) -> Dict[str, Any]:
        metrics = self._health.get_extended_metrics()
        diag = {}
        if self._broadcaster:
            try:
                diag["broadcaster"] = self._broadcaster.get_diagnostics()
                diag["broadcast_metrics"] = self._broadcaster.get_broadcast_metrics()
            except Exception:
                pass
        if self._dashboard_api:
            try:
                diag["dashboard_api"] = self._dashboard_api.get_diagnostics()
            except Exception:
                pass
        if hasattr(self._ws_manager, "get_metrics"):
            try:
                diag["websocket"] = self._ws_manager.get_metrics()
            except Exception:
                pass
        metrics["diagnostics"] = diag
        return APIResponse(data=metrics).to_dict()

    def get_decisions(
        self,
        page: int = 1,
        page_size: int = 10,
        decision: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        score_min: Optional[float] = None,
        score_max: Optional[float] = None,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        _validate_pagination(page, page_size)
        sort_by, sort_order = _validate_sort(sort_by, sort_order)

        all_history = self._engine.get_decision_history(n=1000)
        filtered = _apply_filters(all_history, decision, score_min, score_max, status, date_from, date_to)
        sorted_items = _apply_sort(filtered, sort_by, sort_order)
        total = len(sorted_items)

        start = (page - 1) * page_size
        end = start + page_size
        page_items = sorted_items[start:end]

        paginated = build_paginated_response(
            items=[_build_decision_response(h) for h in page_items],
            total=total,
            page=page,
            page_size=page_size,
        )
        return APIResponse(data=paginated.to_dict()).to_dict()

    def get_decision_by_id(self, signal_id: int) -> Dict[str, Any]:
        history = self._engine.get_decision_history(n=1000)
        for h in history:
            if h["signal_id"] == signal_id:
                return APIResponse(data=h).to_dict()
        raise NotFoundError(f"Decision for signal {signal_id} not found")

    def get_intelligence(self) -> Dict[str, Any]:
        result = self._engine.intelligence.evaluate()
        fusion = result.get("_fusion", {})
        report = self._engine.intelligence.get_fusion_report()
        response = IntelligenceResponse(
            unified_score=fusion.get("unified_score", 50.0),
            module_scores=fusion.get("module_scores", {}),
            health=fusion.get("health", {}),
            report=report,
        )
        return APIResponse(data=response.to_dict()).to_dict()

    def get_features(self) -> Dict[str, Any]:
        features = self._engine.intelligence.get_all_features()
        return APIResponse(data=features).to_dict()

    def get_modules(self) -> Dict[str, Any]:
        diag = self._engine.intelligence.get_diagnostics()
        return APIResponse(data=diag).to_dict()

    def get_portfolio(self) -> Dict[str, Any]:
        detail = self._portfolio.get_portfolio()
        return APIResponse(data=detail.to_dict()).to_dict()

    def get_portfolio_summary(self) -> Dict[str, Any]:
        summary = self._portfolio.get_portfolio_summary()
        return APIResponse(data=summary.to_dict()).to_dict()

    def get_equity_curve(self, limit: int = 100) -> Dict[str, Any]:
        curve = self._portfolio.get_equity_curve(limit=limit)
        return APIResponse(data={"points": curve}).to_dict()

    def get_intelligence_detail(self) -> Dict[str, Any]:
        detail = self._intel.get_intelligence()
        return APIResponse(data=detail.to_dict()).to_dict()

    def get_notifications(
        self,
        limit: int = 50,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        unread_only: bool = False,
        min_priority: Optional[int] = None,
    ) -> Dict[str, Any]:
        history = self._notifications.get_history(
            limit=limit, category=category, severity=severity,
            unread_only=unread_only, min_priority=min_priority,
        )
        return APIResponse(data={"notifications": [n.to_dict() for n in history]}).to_dict()

    def create_notification(self, type: str = "info", category: str = "general", title: str = "",
                           message: str = "", severity: str = "low", priority: int = 0) -> Dict[str, Any]:
        notif = self._notifications.notify(
            type=type, category=category, title=title,
            message=message, severity=severity, priority=priority,
        )
        return APIResponse(data=notif.to_dict()).to_dict()

    def mark_notification_read(self, notification_id: str) -> Dict[str, Any]:
        ok = self._notifications.mark_read(notification_id)
        if not ok:
            raise NotFoundError(f"Notification {notification_id} not found or already read")
        return APIResponse(data={"id": notification_id, "read": True}).to_dict()

    def mark_all_notifications_read(self) -> Dict[str, Any]:
        count = self._notifications.mark_all_read()
        return APIResponse(data={"marked_read": count}).to_dict()

    def get_alert_summary(self) -> Dict[str, Any]:
        summary = self._notifications.get_alert_summary()
        return APIResponse(data=summary.to_dict()).to_dict()

    def get_notification_categories(self) -> Dict[str, Any]:
        categories = self._notifications.get_categories()
        return APIResponse(data={"categories": categories}).to_dict()

    def get_dashboard_overview(self, force_refresh: bool = False) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return APIResponse(data=DashboardOverviewDTO().to_dict()).to_dict()
        overview = self._dashboard_api.get_overview(force_refresh=force_refresh)
        return APIResponse(data=overview.to_dict()).to_dict()

    def get_dashboard_widgets(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return APIResponse(data={"widgets": []}).to_dict()
        widgets = self._dashboard_api.get_widgets()
        return APIResponse(data={"widgets": widgets}).to_dict()

    def get_dashboard_kpis(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return APIResponse(data={}).to_dict()
        kpis = self._dashboard_api.get_kpis()
        return APIResponse(data=kpis).to_dict()

    def get_dashboard_intelligence(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return self.get_intelligence()
        data = self._dashboard_api.get_intelligence_overview()
        return APIResponse(data=data).to_dict()

    def get_dashboard_market(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return self.get_features()
        data = self._dashboard_api.get_market_overview()
        return APIResponse(data=data).to_dict()

    def get_dashboard_risk(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return APIResponse(data={}).to_dict()
        data = self._dashboard_api.get_risk_overview()
        return APIResponse(data=data).to_dict()

    def get_dashboard_portfolio(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return self.get_portfolio()
        data = self._dashboard_api.get_portfolio_overview()
        return APIResponse(data=data).to_dict()

    def get_dashboard_notifications(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return self.get_alert_summary()
        data = self._dashboard_api.get_notification_overview()
        return APIResponse(data=data).to_dict()

    def get_dashboard_monitoring(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return self.get_metrics()
        data = self._dashboard_api.get_monitoring_overview()
        return APIResponse(data=data).to_dict()

    def get_dashboard_performance(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return APIResponse(data={}).to_dict()
        data = self._dashboard_api.get_performance_overview()
        return APIResponse(data=data).to_dict()

    def get_dashboard_diagnostics(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return APIResponse(data={}).to_dict()
        data = self._dashboard_api.get_diagnostics()
        return APIResponse(data=data).to_dict()

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        if self._dashboard_api is None:
            return APIResponse(data={}).to_dict()
        data = self._dashboard_api.get_metrics()
        return APIResponse(data=data.to_dict()).to_dict()

    def get_preferences(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        prefs = self._user_service.get_preferences(uid)
        return APIResponse(data=prefs.to_dict()).to_dict()

    def update_preferences(self, user_id: Optional[str] = None, **updates) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        prefs = self._user_service.update_preferences(uid, updates)
        return APIResponse(data=prefs.to_dict()).to_dict()

    def set_theme(self, theme: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        ok = self._user_service.set_theme(uid, theme)
        return APIResponse(data={"theme": theme, "applied": ok}).to_dict()

    def set_language(self, language: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        self._user_service.set_language(uid, language)
        return APIResponse(data={"language": language}).to_dict()

    def get_layouts(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        layouts = self._user_service.get_layouts(uid)
        return APIResponse(data={"layouts": layouts}).to_dict()

    def save_layout(self, user_id: Optional[str] = None, name: str = "default", widgets: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        layout = self._user_service.save_layout(uid, name, widgets or [])
        return APIResponse(data=layout.to_dict()).to_dict()

    def delete_layout(self, layout_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        ok = self._user_service.delete_layout(uid, layout_id)
        if not ok:
            raise NotFoundError(f"Layout {layout_id} not found")
        return APIResponse(data={"deleted": True, "layout_id": layout_id}).to_dict()

    def get_presets(self) -> Dict[str, Any]:
        presets = self._user_service.get_presets()
        return APIResponse(data={"presets": presets}).to_dict()

    def set_preset(self, preset_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        ok = self._user_service.set_active_preset(uid, preset_id)
        if not ok:
            raise NotFoundError(f"Preset {preset_id} not found")
        return APIResponse(data={"preset": preset_id, "applied": True}).to_dict()

    def get_favorites(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        symbols = self._user_service.get_favorites(uid)
        return APIResponse(data={"symbols": symbols}).to_dict()

    def add_favorite(self, symbol: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        symbols = self._user_service.add_favorite(uid, symbol)
        return APIResponse(data={"symbols": symbols}).to_dict()

    def remove_favorite(self, symbol: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        symbols = self._user_service.remove_favorite(uid, symbol)
        return APIResponse(data={"symbols": symbols}).to_dict()

    def get_watchlist(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        symbols = self._user_service.get_watchlist(uid)
        return APIResponse(data={"symbols": symbols}).to_dict()

    def add_to_watchlist(self, symbol: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        symbols = self._user_service.add_to_watchlist(uid, symbol)
        return APIResponse(data={"symbols": symbols}).to_dict()

    def remove_from_watchlist(self, symbol: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        symbols = self._user_service.remove_from_watchlist(uid, symbol)
        return APIResponse(data={"symbols": symbols}).to_dict()

    def get_recent_activity(self, limit: int = 20) -> Dict[str, Any]:
        activity = self._user_service.get_recent_activity(limit=limit)
        return APIResponse(data={"activities": activity}).to_dict()

    def create_session(self, user_id: Optional[str] = None, ip_address: str = "", user_agent: str = "") -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        session = self._user_service.create_session(uid, ip_address, user_agent)
        return APIResponse(data=session.to_dict()).to_dict()

    def get_session(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        uid = self._require_user_id(user_id)
        session = self._user_service.get_session(uid)
        if session is None:
            return APIResponse(data={}).to_dict()
        return APIResponse(data=session.to_dict()).to_dict()
