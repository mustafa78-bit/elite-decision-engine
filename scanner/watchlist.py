"""WatchlistEngine — manage and filter opportunities by watchlist."""

from __future__ import annotations

import logging
from typing import Any, Optional

from scanner.models import Opportunity

logger = logging.getLogger(__name__)


class WatchlistEngine:
    """Filter opportunities to user-defined watchlists."""

    def __init__(self) -> None:
        self._watchlist: dict[str, list[str]] = {}
        self._active: str = ""

    def create(self, name: str, symbols: Optional[list[str]] = None) -> dict[str, Any]:
        if name in self._watchlist:
            return {"error": f"Watchlist '{name}' already exists"}
        self._watchlist[name] = list(symbols or [])
        if not self._active:
            self._active = name
        return {"name": name, "symbols": self._watchlist[name], "count": len(self._watchlist[name])}

    def get(self, name: Optional[str] = None) -> dict[str, Any]:
        name = name or self._active
        wl = self._watchlist.get(name)
        if wl is None:
            return {"error": f"Watchlist '{name}' not found"}
        return {"name": name, "symbols": wl, "count": len(wl)}

    def add_symbol(self, symbol: str, name: Optional[str] = None) -> dict[str, Any]:
        name = name or self._active
        wl = self._watchlist.get(name)
        if wl is None:
            return {"error": f"Watchlist '{name}' not found"}
        if symbol not in wl:
            wl.append(symbol)
        return {"name": name, "symbols": wl, "count": len(wl)}

    def remove_symbol(self, symbol: str, name: Optional[str] = None) -> dict[str, Any]:
        name = name or self._active
        wl = self._watchlist.get(name)
        if wl is None:
            return {"error": f"Watchlist '{name}' not found"}
        if symbol in wl:
            wl.remove(symbol)
        return {"name": name, "symbols": wl, "count": len(wl)}

    def list_all(self) -> list[dict[str, Any]]:
        return [
            {"name": k, "symbols": v, "count": len(v), "active": k == self._active}
            for k, v in self._watchlist.items()
        ]

    def set_active(self, name: str) -> dict[str, Any]:
        if name not in self._watchlist:
            return {"error": f"Watchlist '{name}' not found"}
        self._active = name
        return {"name": name, "symbols": self._watchlist[name], "count": len(self._watchlist[name]), "active": True}

    @property
    def active_symbols(self) -> list[str]:
        return self._watchlist.get(self._active, [])

    def filter_opportunities(self, opportunities: list[Opportunity], name: Optional[str] = None) -> list[Opportunity]:
        symbols = self._watchlist.get(name or self._active, [])
        if not symbols:
            return opportunities
        return [o for o in opportunities if o.symbol in symbols]
