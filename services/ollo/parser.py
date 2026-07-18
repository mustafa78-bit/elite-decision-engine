from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class OLLOResponse:
    text: str
    room: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    provider: str = ""
    model: str = ""
    duration_ms: float = 0.0
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    sections: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "room": self.room,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model": self.model,
            "duration_ms": round(self.duration_ms, 2),
            "tokens": {
                "in": self.tokens_in,
                "out": self.tokens_out,
            },
            "sections": self.sections,
        }


@dataclass
class OLLOBriefing:
    kind: str
    title: str
    text: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    provider: str = ""
    model: str = ""
    duration_ms: float = 0.0
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "title": self.title,
            "text": self.text,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model": self.model,
            "duration_ms": round(self.duration_ms, 2),
            "tokens": {
                "in": self.tokens_in,
                "out": self.tokens_out,
            },
        }


KIND_TITLES: dict[str, str] = {
    "morning": "Morning Briefing",
    "evening": "Evening Briefing",
    "market_update": "Market Update",
    "emergency": "Emergency Brief",
    "mission": "Mission Briefing",
}

SECTIONS_PATTERN = re.compile(r"^(#{1,3}\s+)(.+)$", re.MULTILINE)
BULLET_PATTERN = re.compile(r"^[\s]*[-*][\s]+(.+)$", re.MULTILINE)


def parse_response(
    raw_text: str,
    room: str = "",
    provider: str = "",
    model: str = "",
    duration_ms: float = 0.0,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
) -> OLLOResponse:
    text = raw_text.strip()
    sections = _extract_sections(text)
    return OLLOResponse(
        text=text,
        room=room,
        provider=provider,
        model=model,
        duration_ms=duration_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        sections=sections,
    )


def parse_briefing(
    kind: str,
    raw_text: str,
    provider: str = "",
    model: str = "",
    duration_ms: float = 0.0,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
) -> OLLOBriefing:
    title = KIND_TITLES.get(kind, "Briefing")
    return OLLOBriefing(
        kind=kind,
        title=title,
        text=raw_text.strip(),
        provider=provider,
        model=model,
        duration_ms=duration_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )


def _extract_sections(text: str) -> list[dict]:
    sections: list[dict] = []
    lines = text.split("\n")
    current_section: Optional[str] = None
    current_bullets: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        heading_match = SECTIONS_PATTERN.match(line)
        if heading_match:
            if current_section is not None:
                sections.append({
                    "heading": current_section,
                    "bullets": list(current_bullets),
                })
                current_bullets = []
            current_section = heading_match.group(2).strip()
            continue
        bullet_match = BULLET_PATTERN.match(line)
        if bullet_match:
            current_bullets.append(bullet_match.group(1).strip())
            continue

    if current_section is not None:
        sections.append({
            "heading": current_section,
            "bullets": list(current_bullets),
        })

    return sections
