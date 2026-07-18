from __future__ import annotations

import logging
from typing import Optional

from config import AI_MODEL, AI_PROVIDER, NVIDIA_API_KEY, NVIDIA_BASE_URL
from services.ai.provider import AIProvider
from services.ai.nvidia_provider import NVIDIAProvider

logger = logging.getLogger(__name__)


def create_provider(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> AIProvider:
    provider_name = (provider or AI_PROVIDER).strip().lower()

    if provider_name == "nvidia":
        logger.info(
            "Creating NVIDIA provider | model=%s",
            model or AI_MODEL or "default",
        )
        return NVIDIAProvider(
            api_key=api_key or NVIDIA_API_KEY,
            base_url=base_url or NVIDIA_BASE_URL or None,
            model=model or AI_MODEL or None,
        )

    if provider_name == "openai":
        raise NotImplementedError(
            "OpenAI provider is not yet implemented. "
            "Set AI_PROVIDER=nvidia to use NVIDIA NIM."
        )

    if provider_name == "ollama":
        raise NotImplementedError(
            "Ollama provider is not yet implemented. "
            "Set AI_PROVIDER=nvidia to use NVIDIA NIM."
        )

    if provider_name == "local":
        raise NotImplementedError(
            "Local LLM provider is not yet implemented. "
            "Set AI_PROVIDER=nvidia to use NVIDIA NIM."
        )

    msg = "Unknown AI_PROVIDER='%s'. Supported: nvidia, openai, ollama, local"
    logger.error(msg, provider_name)
    raise ValueError(msg % provider_name)


def create_ai_service() -> "AIService":
    from services.ai.ai_service import AIService

    provider = create_provider()
    return AIService(provider)
