from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MEMORY_FILE_PATH = "/app/nexus_permanent_memory.json"


@dataclass
class ConceptMemory:
    """Strongly typed representation of permanent NEXUS knowledge."""

    founder_preferences: Dict[str, Any] = field(
        default_factory=lambda: {
            "name": "Founder",
            "favorite_markets": ["BTC", "ETH"],
            "ui_layout": "Command Deck",
        }
    )
    risk_preferences: Dict[str, Any] = field(
        default_factory=lambda: {
            "risk_profile": "moderate",
            "max_exposure_limit": 50000.0,
            "max_daily_loss_limit": 500.0,
        }
    )
    strategy_preferences: Dict[str, Any] = field(
        default_factory=lambda: {
            "preferred_strategies": ["ema_cross", "breakout"],
            "favorite_indicators": ["EMA", "RSI", "ATR"],
            "default_timeframe": "1h",
        }
    )
    observed_behaviors: List[str] = field(
        default_factory=lambda: [
            "Prefers entering positions during high volatility regimes.",
            "Tends to monitor open trades more heavily during weekends.",
        ]
    )
    repeated_mistakes: List[str] = field(
        default_factory=lambda: [
            "Entering trades without waiting for BTC health validation.",
            "Widening stop losses on short-term trend reversals.",
        ]
    )
    successful_patterns: List[str] = field(
        default_factory=lambda: [
            "Strictly taking profit at predetermined TP1 and TP2 levels.",
            "De-risking portfolio when market regime transitions to highly volatile/bearish.",
        ]
    )
    long_term_objectives: Dict[str, Any] = field(
        default_factory=lambda: {
            "monthly_return_target_pct": 10.0,
            "max_drawdown_tolerance_pct": 5.0,
        }
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MemoryLayer:
    """Manages permanent NEXUS memories around concepts, keeping them separate from ephemeral session contexts."""

    _instance: Optional[MemoryLayer] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._memory = ConceptMemory()
        self.load()
        self._initialized = True

    @property
    def memory(self) -> ConceptMemory:
        return self._memory

    def load(self) -> None:
        """Load conceptual memories from permanent file storage."""
        if os.path.exists(MEMORY_FILE_PATH):
            try:
                with open(MEMORY_FILE_PATH, "r") as f:
                    data = json.load(f)
                self._memory = ConceptMemory(
                    founder_preferences=data.get("founder_preferences", self._memory.founder_preferences),
                    risk_preferences=data.get("risk_preferences", self._memory.risk_preferences),
                    strategy_preferences=data.get("strategy_preferences", self._memory.strategy_preferences),
                    observed_behaviors=data.get("observed_behaviors", self._memory.observed_behaviors),
                    repeated_mistakes=data.get("repeated_mistakes", self._memory.repeated_mistakes),
                    successful_patterns=data.get("successful_patterns", self._memory.successful_patterns),
                    long_term_objectives=data.get("long_term_objectives", self._memory.long_term_objectives),
                )
                logger.info("NEXUS Permanent Memory loaded successfully.")
            except Exception as e:
                logger.exception("Failed to load NEXUS Permanent Memory; using defaults.")

    def save(self) -> None:
        """Save conceptual memories to permanent file storage."""
        try:
            with open(MEMORY_FILE_PATH, "w") as f:
                json.dump(self._memory.to_dict(), f, indent=2)
            logger.info("NEXUS Permanent Memory saved successfully.")
        except Exception as e:
            logger.exception("Failed to save NEXUS Permanent Memory.")

    def add_repeated_mistake(self, mistake: str) -> None:
        """Add a newly identified repeated mistake."""
        if mistake and mistake not in self._memory.repeated_mistakes:
            self._memory.repeated_mistakes.append(mistake)
            self.save()

    def add_successful_pattern(self, pattern: str) -> None:
        """Add a newly identified successful pattern."""
        if pattern and pattern not in self._memory.successful_patterns:
            self._memory.successful_patterns.append(pattern)
            self.save()

    def add_observed_behavior(self, behavior: str) -> None:
        """Add an observed behavior pattern."""
        if behavior and behavior not in self._memory.observed_behaviors:
            self._memory.observed_behaviors.append(behavior)
            self.save()

    def update_founder_preferences(self, prefs: Dict[str, Any]) -> None:
        """Update part or all of founder preferences."""
        self._memory.founder_preferences.update(prefs)
        self.save()

    def update_risk_preferences(self, prefs: Dict[str, Any]) -> None:
        """Update risk preferences."""
        self._memory.risk_preferences.update(prefs)
        self.save()

    def update_strategy_preferences(self, prefs: Dict[str, Any]) -> None:
        """Update strategy preferences."""
        self._memory.strategy_preferences.update(prefs)
        self.save()

    def update_long_term_objectives(self, objectives: Dict[str, Any]) -> None:
        """Update long-term objectives."""
        self._memory.long_term_objectives.update(objectives)
        self.save()


# Global singleton instance
memory_layer = MemoryLayer()
