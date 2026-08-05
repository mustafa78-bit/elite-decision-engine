from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class WatchlistDTO:
    id: int | None = None
    user_id: int | None = None
    name: str = "Default"
    symbols: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WatchlistCreateDTO:
    name: str = "Default"
    symbols: list[str] = field(default_factory=list)


@dataclass
class WatchlistUpdateDTO:
    name: str | None = None
    symbols: list[str] | None = None
    add_symbols: list[str] | None = None
    remove_symbols: list[str] | None = None
