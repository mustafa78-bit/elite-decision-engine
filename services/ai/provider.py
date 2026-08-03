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
    error: str | None = None


@dataclass
class GenerationResult:
    content: str
    model: str
    provider: str
    duration_ms: float
    tokens_in: int | None = None
    tokens_out: int | None = None
    retries: int = 0
    error: str | None = None


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
