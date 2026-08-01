from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    connected: bool
    model: str
    latency_ms: float
    provider: str
    error: Optional[str] = None


@dataclass
class GenerationResult:
    content: str
    model: str
    provider: str
    duration_ms: float
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    retries: int = 0
    error: Optional[str] = None


class AIProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        ...

    @abstractmethod
    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> GenerationResult:
        ...

    @abstractmethod
    def health(self) -> HealthStatus:
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        ...
