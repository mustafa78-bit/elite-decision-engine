import pytest
from dataclasses import dataclass, fields, is_dataclass, MISSING
from typing import Any, Dict, List, Optional

from api.schemas import APIResponse, APIError, PaginatedResponse, DecisionResponse, IntelligenceResponse, build_paginated_response
from api.websocket import WSEvent, WSEventType, WSNotificationPayload, WSDashboardPayload, WSSubscriptionPayload
from dto.models import (
    PortfolioDTO, TradeDTO, EquityPointDTO, PortfolioDetailsDTO,
    IntelligenceDTO, MarketRegimeDTO, IntelligenceDetailsDTO,
    RiskDTO, MonitoringDTO, NotificationDTO, AlertSummaryDTO,
    WidgetDTO, KPIDTO, DashboardOverviewDTO, MarketOverviewDTO,
    DashboardMetricsDTO, WebSocketDTO, DashboardDTO,
)
from core.health import HealthStatus, MetricsResponse
from core.serialization import SerializableMixin, serialize_list
from services.real_time import Subscription, EventBatch
from whale.smart_money import SmartMoneyWallet


_ALL_DTO_CLASSES = [
    PortfolioDTO, TradeDTO, EquityPointDTO, PortfolioDetailsDTO,
    IntelligenceDTO, MarketRegimeDTO, IntelligenceDetailsDTO,
    RiskDTO, MonitoringDTO, NotificationDTO, AlertSummaryDTO,
    WidgetDTO, KPIDTO, DashboardOverviewDTO, MarketOverviewDTO,
    DashboardMetricsDTO, WebSocketDTO, DashboardDTO,
    HealthStatus, MetricsResponse,
    DecisionResponse, IntelligenceResponse,
    WSEvent, WSNotificationPayload, WSDashboardPayload, WSSubscriptionPayload,
    Subscription, EventBatch, SmartMoneyWallet,
]

_SERIALIZABLE_MIXIN_CLASSES = [
    PortfolioDTO, TradeDTO, EquityPointDTO,
    IntelligenceDTO, MarketRegimeDTO,
    RiskDTO, MonitoringDTO, NotificationDTO, AlertSummaryDTO,
    WidgetDTO, KPIDTO, MarketOverviewDTO, DashboardMetricsDTO, WebSocketDTO,
]

_SIMPLE_DTOS_WITH_TO_DICT = [
    PortfolioDetailsDTO, IntelligenceDetailsDTO, DashboardOverviewDTO, DashboardDTO,
    HealthStatus, MetricsResponse,
    DecisionResponse, IntelligenceResponse,
    WSEvent, WSNotificationPayload, WSDashboardPayload, WSSubscriptionPayload,
    Subscription, EventBatch, SmartMoneyWallet,
]


def _instantiate(cls):
    kwargs = {}
    if is_dataclass(cls):
        for f in fields(cls):
            if f.default is not MISSING:
                continue
            kwargs[f.name] = _default_for_type(f.type)
    return cls(**kwargs)


def _default_for_type(tp):
    if tp in (str,):
        return ""
    if tp in (int, float):
        return 0
    if tp is bool:
        return False
    if tp is list or getattr(tp, "__origin__", None) is list:
        return []
    if tp is dict or getattr(tp, "__origin__", None) is dict:
        return {}
    if tp is set or getattr(tp, "__origin__", None) is set:
        return set()
    if is_dataclass(tp):
        return _instantiate(tp)
    return None


class TestAllDTOsHaveToDict:

    @pytest.mark.parametrize("cls", _ALL_DTO_CLASSES)
    def test_has_to_dict_method(self, cls):
        assert hasattr(cls, "to_dict"), f"{cls.__name__} missing to_dict"
        assert callable(getattr(cls, "to_dict")), f"{cls.__name__}.to_dict not callable"

    @pytest.mark.parametrize("cls", _ALL_DTO_CLASSES)
    def test_to_dict_returns_dict(self, cls):
        try:
            instance = _instantiate(cls)
        except Exception:
            special = {
                DecisionResponse: DecisionResponse(signal_id=0, decision="", score=0.0, confidence=0.0, confidence_label="", reasons={}, timestamp=""),
                IntelligenceResponse: IntelligenceResponse(unified_score=0.0, module_scores={}, health={}, report={}),
                WSEvent: WSEvent(event_type=WSEventType.HEALTH, data={}),
                Subscription: Subscription(connection_id="test"),
                SmartMoneyWallet: SmartMoneyWallet(address="test"),
            }
            instance = special.get(cls, cls())
        result = instance.to_dict()
        assert isinstance(result, dict), f"{cls.__name__}.to_dict() returned {type(result)}"


class TestSerializationContract:

    def test_serialize_list(self):
        items = [PortfolioDTO(total_trades=1), PortfolioDTO(total_trades=2)]
        result = serialize_list(items)
        assert len(result) == 2
        assert result[0]["total_trades"] == 1
        assert result[1]["total_trades"] == 2

    def test_serialize_list_mixed(self):
        result = serialize_list([{"a": 1}, PortfolioDTO(total_trades=3)])
        assert result[0] == {"a": 1}
        assert result[1]["total_trades"] == 3

    @pytest.mark.parametrize("cls", _SERIALIZABLE_MIXIN_CLASSES)
    def test_serializable_mixin_to_dict_uses_asdict(self, cls):
        instance = cls()
        d = instance.to_dict()
        for f in fields(cls):
            assert f.name in d, f"{cls.__name__}.to_dict() missing field '{f.name}'"

    @pytest.mark.parametrize("cls", _SERIALIZABLE_MIXIN_CLASSES)
    def test_serializable_mixin_from_dict(self, cls):
        instance = cls()
        d = instance.to_dict()
        restored = cls.from_dict(d)
        assert isinstance(restored, cls)


class TestAPIResponseContract:

    def test_api_response_success_shape(self):
        r = APIResponse(data={"key": "value"})
        d = r.to_dict()
        assert d["success"] is True
        assert d["data"] == {"key": "value"}
        assert "version" in d
        assert "timestamp" in d

    def test_api_response_error_shape(self):
        err = APIError(code="NOT_FOUND", message="Item not found")
        r = APIResponse(success=False, error=err)
        d = r.to_dict()
        assert d["success"] is False
        assert d["error"]["code"] == "NOT_FOUND"
        assert d["error"]["message"] == "Item not found"
        assert "data" not in d

    def test_api_response_request_id(self):
        r = APIResponse(data={}, request_id="req-123")
        d = r.to_dict()
        assert d["request_id"] == "req-123"

    def test_api_response_request_id_omitted_when_empty(self):
        r = APIResponse(data={})
        d = r.to_dict()
        assert "request_id" not in d

    def test_api_error_filters_none_details(self):
        err = APIError(code="ERR", message="msg")
        d = err.to_dict()
        assert "details" not in d

    def test_api_error_includes_details(self):
        err = APIError(code="ERR", message="msg", details={"field": "value"})
        d = err.to_dict()
        assert d["details"] == {"field": "value"}


class TestPaginatedResponseContract:

    def test_paginated_response_shape(self):
        r = build_paginated_response(items=[1, 2, 3], total=10, page=1, page_size=3)
        d = r.to_dict()
        assert d["items"] == [1, 2, 3]
        assert d["total"] == 10
        assert d["page"] == 1
        assert d["page_size"] == 3
        assert d["total_pages"] == 4
        assert d["has_next"] is True
        assert d["has_prev"] is False
        assert d["next_page"] == 2
        assert d["prev_page"] is None

    def test_paginated_response_last_page(self):
        r = build_paginated_response(items=[], total=10, page=4, page_size=3)
        d = r.to_dict()
        assert d["has_next"] is False
        assert d["next_page"] is None
        assert d["has_prev"] is True
        assert d["prev_page"] == 3

    def test_paginated_response_single_page(self):
        r = build_paginated_response(items=[1], total=1, page=1, page_size=10)
        d = r.to_dict()
        assert d["total_pages"] == 1
        assert d["has_next"] is False
        assert d["has_prev"] is False

    def test_paginated_response_zero_items(self):
        r = build_paginated_response(items=[], total=0, page=1, page_size=10)
        d = r.to_dict()
        assert d["total_pages"] == 1
        assert d["items"] == []


class TestWebSocketPayloadContract:

    def test_wsevent_envelope_shape(self):
        e = WSEvent(event_type=WSEventType.HEALTH, data={"status": "ok"})
        d = e.to_dict()
        assert d["event_type"] == "health"
        assert d["data"] == {"status": "ok"}
        assert d["version"] == "2.0"
        assert "timestamp" in d
        assert "event_id" in d

    def test_wsevent_all_types_have_valid_event_type(self):
        for et in WSEventType:
            e = WSEvent(event_type=et, data={})
            d = e.to_dict()
            assert d["event_type"] in {t.value for t in WSEventType}

    def test_wsnotification_payload_shape(self):
        p = WSNotificationPayload(type="warning", title="Test", message="Msg", severity="high")
        d = p.to_dict()
        assert d["type"] == "warning"
        assert d["title"] == "Test"
        assert d["message"] == "Msg"
        assert d["severity"] == "high"

    def test_wsdashboard_payload_shape(self):
        p = WSDashboardPayload(portfolio={"trades": 5}, intelligence={"score": 80.0})
        d = p.to_dict()
        assert d["portfolio"] == {"trades": 5}
        assert d["intelligence"] == {"score": 80.0}
        assert d["risk"] == {}
        assert d["monitoring"] == {}

    def test_wssubscription_payload_shape(self):
        p = WSSubscriptionPayload(topic="dashboard", action="subscribe", connection_id="conn1")
        d = p.to_dict()
        assert d["topic"] == "dashboard"
        assert d["action"] == "subscribe"
        assert d["connection_id"] == "conn1"


class TestWebSocketDTOContract:

    def test_websocket_dto_version(self):
        dto = WebSocketDTO()
        assert dto.version == "2.0", "WebSocketDTO.version must be 2.0 to match WSEvent"

    def test_websocket_dto_shape(self):
        dto = WebSocketDTO(event="decision", data={"id": 1})
        d = dto.to_dict()
        assert d["event"] == "decision"
        assert d["data"] == {"id": 1}
        assert d["version"] == "2.0"

    def test_websocket_dto_defaults(self):
        dto = WebSocketDTO()
        d = dto.to_dict()
        assert d["event"] == ""
        assert d["data"] == {}
        assert d["version"] == "2.0"


class TestDecisionResponseContract:

    def test_decision_response_shape(self):
        r = DecisionResponse(
            signal_id=1, decision="APPROVED", score=85.5,
            confidence=75.0, confidence_label="HIGH",
            reasons={"approval": ["good"], "rejection": []},
            timestamp="2026-01-01T00:00:00Z",
        )
        d = r.to_dict()
        assert d["signal_id"] == 1
        assert d["decision"] == "APPROVED"
        assert d["score"] == 85.5
        assert d["confidence"] == 75.0
        assert d["confidence_label"] == "HIGH"
        assert d["reasons"]["approval"] == ["good"]
        assert "timestamp" in d

    def test_intelligence_response_shape(self):
        r = IntelligenceResponse(
            unified_score=72.0,
            module_scores={"whale": 85.0},
            health={"whale": True},
            report={"fusion": "ok"},
        )
        d = r.to_dict()
        assert d["unified_score"] == 72.0
        assert d["module_scores"] == {"whale": 85.0}
        assert d["health"] == {"whale": True}
        assert d["report"] == {"fusion": "ok"}


class TestHealthDTOContract:

    def test_health_status_shape(self):
        h = HealthStatus(status="healthy", modules={"whale": True}, database="connected", uptime_seconds=100.0)
        d = h.to_dict()
        assert d["status"] == "healthy"
        assert d["modules"] == {"whale": True}
        assert d["database"] == "connected"
        assert d["uptime_seconds"] == 100.0
        assert d["version"] == "1.0.0"
        assert "timestamp" in d

    def test_metrics_response_shape(self):
        m = MetricsResponse(evaluate_calls=10, modules_active=3, decisions_made=5, signals_processed=5)
        d = m.to_dict()
        assert d["evaluate_calls"] == 10
        assert d["modules_active"] == 3
        assert d["decisions_made"] == 5
        assert d["signals_processed"] == 5


class TestRealTimeDTOContract:

    def test_subscription_to_dict(self):
        s = Subscription(connection_id="conn1", channels={"dashboard", "health"})
        d = s.to_dict()
        assert d["connection_id"] == "conn1"
        assert "dashboard" in d["channels"]
        assert "health" in d["channels"]
        assert "created_at" in d

    def test_event_batch_to_dict(self):
        events = [WSEvent(event_type=WSEventType.HEALTH, data={"s": "ok"})]
        b = EventBatch(events=events, channel="health")
        d = b.to_dict()
        assert d["channel"] == "health"
        assert d["count"] == 1
        assert d["events"][0]["event_type"] == "health"
        assert d["events"][0]["data"] == {"s": "ok"}


class TestSmartMoneyWalletContract:

    def test_smart_money_wallet_to_dict(self):
        w = SmartMoneyWallet(address="0xabc", reputation_score=85.0, total_volume_usd=50000.0, total_transfers=10)
        d = w.to_dict()
        assert d["address"] == "0xabc"
        assert d["reputation_score"] == 85.0
        assert d["total_volume_usd"] == 50000.0
        assert d["total_transfers"] == 10
        assert d["behavior_type"] == "UNKNOWN"
        assert d["tags"] == []

    def test_smart_money_wallet_defaults(self):
        w = SmartMoneyWallet(address="0xdef")
        d = w.to_dict()
        assert d["address"] == "0xdef"
        assert d["reputation_score"] == 50.0
        assert d["first_seen"] is None


class TestDTOFieldCompleteness:

    @pytest.mark.parametrize("cls", _SERIALIZABLE_MIXIN_CLASSES)
    def test_all_fields_included_in_to_dict(self, cls):
        instance = cls()
        d = instance.to_dict()
        for f in fields(cls):
            if f.name.startswith("_"):
                continue
            assert f.name in d, f"{cls.__name__}.to_dict() missing '{f.name}'"

    @pytest.mark.parametrize("cls", _SIMPLE_DTOS_WITH_TO_DICT)
    def test_all_dataclass_fields_in_custom_to_dict(self, cls):
        if not is_dataclass(cls):
            return
        try:
            instance = cls()
        except TypeError:
            _CTOR = {
                DecisionResponse: lambda: DecisionResponse(signal_id=0, decision="", score=0.0, confidence=0.0, confidence_label="", reasons={}, timestamp=""),
                IntelligenceResponse: lambda: IntelligenceResponse(unified_score=0.0, module_scores={}, health={}, report={}),
                WSEvent: lambda: WSEvent(event_type=WSEventType.HEALTH, data={}),
                Subscription: lambda: Subscription(connection_id="test"),
                SmartMoneyWallet: lambda: SmartMoneyWallet(address="test"),
            }
            instance = _CTOR[cls]()
        d = instance.to_dict()
        for f in fields(cls):
            if f.name.startswith("_"):
                continue
            assert f.name in d, f"{cls.__name__}.to_dict() missing field '{f.name}'"


class TestBackwardCompatibility:

    def test_dashboard_dto_backward_compat(self):
        dto = DashboardDTO()
        d = dto.to_dict()
        assert "portfolio" in d
        assert "intelligence" in d
        assert "risk" in d
        assert "monitoring" in d
        assert "recent_decisions" in d
        assert "recent_notifications" in d

    def test_dashboard_overview_dto_backward_compat(self):
        dto = DashboardOverviewDTO()
        d = dto.to_dict()
        assert "portfolio" in d
        assert "intelligence" in d
        assert "risk" in d
        assert "monitoring" in d
        assert "notifications" in d
        assert "performance" in d

    def test_portfolio_details_dto_backward_compat(self):
        dto = PortfolioDetailsDTO()
        d = dto.to_dict()
        assert "summary" in d
        assert "equity_curve" in d
        assert "daily_pnl" in d
        assert "unrealized_pnl" in d
        assert "realized_pnl" in d
        assert "profit_factor" in d
        assert "exposure" in d
        assert "asset_allocation" in d
        assert "position_summary" in d

    def test_intelligence_details_dto_backward_compat(self):
        dto = IntelligenceDetailsDTO()
        d = dto.to_dict()
        assert "summary" in d
        assert "ai_confidence" in d
        assert "funding_summary" in d
        assert "open_interest_summary" in d
        assert "whale_summary" in d
        assert "liquidity_summary" in d
        assert "orderflow_summary" in d
        assert "market_regime" in d
        assert "trend_summary" in d
        assert "signal_summary" in d

    def test_portfolio_dto_fields(self):
        dto = PortfolioDTO(total_trades=10, win_rate=65.5)
        d = dto.to_dict()
        assert d["total_trades"] == 10
        assert d["win_rate"] == 65.5

    def test_trade_dto_fields(self):
        dto = TradeDTO(id=1, symbol="BTC", side="LONG")
        d = dto.to_dict()
        assert d["id"] == 1
        assert d["symbol"] == "BTC"
        assert d["side"] == "LONG"
