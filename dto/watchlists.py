from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Optional


@dataclass
class WatchlistDTO:
    id: Optional[int] = None
    user_id: Optional[int] = None
    name: str = "Default"
    symbols: list[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WatchlistCreateDTO:
    name: str = "Default"
    symbols: list[str] = field(default_factory=list)


@dataclass
class WatchlistUpdateDTO:
    name: Optional[str] = None
    symbols: Optional[list[str]] = None
    add_symbols: Optional[list[str]] = None
    remove_symbols: Optional[list[str]] = None
