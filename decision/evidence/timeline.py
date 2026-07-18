from __future__ import annotations

from datetime import datetime
from typing import Any

from decision.evidence.dto import EvidenceItem


def build_timeline(items: list[EvidenceItem]) -> list[EvidenceItem]:
    with_ts = [i for i in items if i.timestamp]
    sorted_items = sorted(with_ts, key=lambda i: _parse_timestamp(i.timestamp))
    return sorted_items


def timeline_summary(items: list[EvidenceItem]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in build_timeline(items):
        ts = _parse_timestamp(item.timestamp)
        time_str = ts.strftime("%H:%M") if ts else "--:--"
        entries.append({
            "time": time_str,
            "timestamp": item.timestamp,
            "title": item.title,
            "description": item.description,
            "engine": item.engine,
            "category": item.category,
            "supports_decision": item.supports_decision,
            "severity": item.severity,
        })
    return entries


def _parse_timestamp(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return datetime.min
