from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


ENGINE_VERSIONS: dict[str, str] = {
    "scanner": "2.4",
    "risk_engine": "1.3",
    "council": "4.0",
    "portfolio": "2.1",
    "market_regime": "1.2",
    "whale": "1.1",
    "explain": "1.0",
    "decision": "3.0",
    "evidence_engine": "1.0",
}


def get_version(engine: str) -> str:
    return ENGINE_VERSIONS.get(engine, "0.0")


@dataclass(frozen=True)
class SourceTrace:
    origin: str
    engine: str
    module_version: str = "0.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision_id: str = ""

    def __post_init__(self) -> None:
        if self.module_version == "0.0":
            object.__setattr__(self, "module_version", ENGINE_VERSIONS.get(self.engine, "0.0"))
        if not self.decision_id:
            object.__setattr__(self, "decision_id", uuid4().hex[:12])

    def to_dict(self) -> dict[str, str]:
        return {
            "origin": self.origin,
            "engine": self.engine,
            "module_version": self.module_version,
            "timestamp": self.timestamp,
            "decision_id": self.decision_id,
        }
