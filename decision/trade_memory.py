from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from decision.models import DecisionSnapshot, TradeOutcome


@dataclass
class TradeMemoryEntry:
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    is_win: bool
    signal_id: int = 0
    strategy_fingerprint: str = ""
    decision_snapshot: Optional[Dict[str, Any]] = None
    entry_conditions: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "is_win": self.is_win,
            "signal_id": self.signal_id,
            "strategy_fingerprint": self.strategy_fingerprint,
            "decision_snapshot": self.decision_snapshot,
            "entry_conditions": dict(self.entry_conditions),
            "tags": list(self.tags),
            "created_at": self.created_at.isoformat(),
        }


class TradeMemoryStore:

    def __init__(self):
        self._entries: List[TradeMemoryEntry] = []
        self._max_entries = 10000

    def store(
        self,
        outcome: TradeOutcome,
        decision_snapshot: Optional[DecisionSnapshot] = None,
    ) -> TradeMemoryEntry:
        entry = TradeMemoryEntry(
            symbol=outcome.symbol,
            side=outcome.side,
            entry_price=outcome.entry_price,
            exit_price=outcome.exit_price,
            pnl=outcome.pnl,
            pnl_pct=outcome.pnl_pct,
            is_win=outcome.is_win(),
            signal_id=outcome.decision_snapshot.signal_id if outcome.decision_snapshot else 0,
            strategy_fingerprint=outcome.strategy_fingerprint,
            decision_snapshot=decision_snapshot.to_dict() if decision_snapshot else None,
            entry_conditions=self._extract_entry_conditions(outcome),
            tags=list(outcome.tags),
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def _extract_entry_conditions(self, outcome: TradeOutcome) -> Dict[str, Any]:
        if outcome.decision_snapshot and outcome.decision_snapshot.context:
            ctx = outcome.decision_snapshot.context
            return {
                "symbol": ctx.signal_symbol,
                "side": ctx.signal_side,
                "base_score": ctx.base_score,
                "factors": [f.to_dict() for f in ctx.factors],
            }
        return {}

    def find_by_symbol(self, symbol: str) -> List[TradeMemoryEntry]:
        return [e for e in self._entries if e.symbol == symbol]

    def find_by_strategy(self, fingerprint: str) -> List[TradeMemoryEntry]:
        return [e for e in self._entries if e.strategy_fingerprint == fingerprint]

    def get_wins(self) -> List[TradeMemoryEntry]:
        return [e for e in self._entries if e.is_win]

    def get_losses(self) -> List[TradeMemoryEntry]:
        return [e for e in self._entries if not e.is_win]

    def win_rate(self) -> float:
        if not self._entries:
            return 0.0
        wins = len(self.get_wins())
        return wins / len(self._entries)

    def average_pnl(self) -> float:
        if not self._entries:
            return 0.0
        return sum(e.pnl for e in self._entries) / len(self._entries)

    def average_pnl_pct(self) -> float:
        if not self._entries:
            return 0.0
        return sum(e.pnl_pct for e in self._entries) / len(self._entries)

    def get_all(self) -> List[TradeMemoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def find_similar(
        self,
        symbol: str = "",
        side: str = "",
        strategy_fingerprint: str = "",
        min_similarity: float = 0.0,
    ) -> List[TradeMemoryEntry]:
        results = list(self._entries)
        if symbol:
            results = [e for e in results if e.symbol == symbol]
        if side:
            results = [e for e in results if e.side == side]
        if strategy_fingerprint:
            results = [
                e for e in results if e.strategy_fingerprint == strategy_fingerprint
            ]
        return results
