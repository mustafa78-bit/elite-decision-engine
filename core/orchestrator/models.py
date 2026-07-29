from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IntelligenceContext(BaseModel):
    """Immutable single context passed sequentially through the ADIP engines."""
    symbol: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_inputs: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)


class IntelligenceResult(BaseModel):
    """Standardized output produced by each intelligence service."""
    engine_name: str
    confidence: float = 0.0  # Normalized: 0.0 to 1.0
    reasoning: str = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    supporting_signals: List[str] = Field(default_factory=list)
    conflicting_signals: List[str] = Field(default_factory=list)
    execution_time: float = 0.0  # Seconds
    status: str = "SUCCESS"


class IntelligenceEvent(BaseModel):
    """Timeline event emitted internally whenever a workflow milestone is met."""
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    symbol: str
    payload: Dict[str, Any] = Field(default_factory=dict)
