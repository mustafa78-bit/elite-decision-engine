from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class APIError:
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


_metadata: Dict[str, Any] = {}


def set_api_metadata(**kwargs):
    _metadata.update(kwargs)


def get_api_metadata() -> Dict[str, Any]:
    return dict(_metadata)


@dataclass
class APIResponse:
    success: bool = True
    data: Optional[Any] = None
    error: Optional[APIError] = None
    version: str = "1.0.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    request_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "success": self.success,
            "version": self.version,
            "timestamp": self.timestamp,
        }
        if self.request_id:
            result["request_id"] = self.request_id
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error.to_dict()
        return result


@dataclass
class PaginatedResponse:
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def next_page(self) -> Optional[int]:
        return self.page + 1 if self.has_next else None

    @property
    def prev_page(self) -> Optional[int]:
        return self.page - 1 if self.has_prev else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
            "next_page": self.next_page,
            "prev_page": self.prev_page,
        }


def build_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@dataclass
class SortParam:
    field: str = "timestamp"
    order: str = "desc"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


from core.health import HealthStatus, MetricsResponse


@dataclass
class DecisionResponse:
    signal_id: int
    decision: str
    score: float
    confidence: float
    confidence_label: str
    reasons: Dict[str, List[str]]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceResponse:
    unified_score: float
    module_scores: Dict[str, float]
    health: Dict[str, bool]
    report: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
