from __future__ import annotations

import logging
import time
from typing import Any, Optional

from services.ai.provider import AIProvider, GenerationResult, HealthStatus

logger = logging.getLogger(__name__)


class AIService:

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    @property
    def provider(self) -> AIProvider:
        return self._provider

    @property
    def model(self) -> str:
        return self._provider.model

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        start = time.perf_counter()
        logger.info(
            "AIService.generate | provider=%s | model=%s",
            self._provider.__class__.__name__, self._provider.model,
        )
        result = self._provider.generate(prompt, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "AIService.generate result | provider=%s | model=%s | duration_ms=%s | "
            "tokens_in=%s | tokens_out=%s | retries=%s | error=%s",
            result.provider, result.model, round(elapsed, 2),
            result.tokens_in, result.tokens_out, result.retries,
            result.error if result.error else "none",
        )
        return result

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> GenerationResult:
        start = time.perf_counter()
        logger.info(
            "AIService.chat | provider=%s | model=%s | messages=%s",
            self._provider.__class__.__name__, self._provider.model, len(messages),
        )
        result = self._provider.chat(messages, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "AIService.chat result | provider=%s | model=%s | duration_ms=%s | "
            "tokens_in=%s | tokens_out=%s | retries=%s | error=%s",
            result.provider, result.model, round(elapsed, 2),
            result.tokens_in, result.tokens_out, result.retries,
            result.error if result.error else "none",
        )
        return result

    def health(self) -> HealthStatus:
        return self._provider.health()
