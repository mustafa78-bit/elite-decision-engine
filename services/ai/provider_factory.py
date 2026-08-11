from __future__ import annotations

import logging
from typing import Optional

import config
from services.ai.provider import AIProvider
from services.ai.nvidia_provider import NVIDIAProvider
from services.ai.multi_nvidia_provider import MultiNVIDIAProvider

logger = logging.getLogger(__name__)


def create_provider(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> AIProvider:
    provider_name = (provider or config.AI_PROVIDER).strip().lower()

    if provider_name == "nvidia":
        if not api_key and config.NVIDIA_API_KEY_2:
            logger.info(
                "Creating multi-key NVIDIA provider (load-splitting) | model=%s",
                model or config.AI_MODEL or "default",
            )
            p1 = NVIDIAProvider(
                api_key=config.NVIDIA_API_KEY,
                base_url=base_url or config.NVIDIA_BASE_URL or None,
                model=model or config.AI_MODEL or None,
            )
            p2 = NVIDIAProvider(
                api_key=config.NVIDIA_API_KEY_2,
                base_url=base_url or config.NVIDIA_BASE_URL or None,
                model=model or config.AI_MODEL or None,
            )
            return MultiNVIDIAProvider(p1, p2)
        else:
            logger.info(
                "Creating single NVIDIA provider | model=%s",
                model or config.AI_MODEL or "default",
            )
            return NVIDIAProvider(
                api_key=api_key or config.NVIDIA_API_KEY,
                base_url=base_url or config.NVIDIA_BASE_URL or None,
                model=model or config.AI_MODEL or None,
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
