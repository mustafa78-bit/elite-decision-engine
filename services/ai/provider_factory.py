from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from config import AI_MODEL, AI_PROVIDER, NVIDIA_API_KEY, NVIDIA_API_KEY_2, NVIDIA_BASE_URL
from services.ai.multi_nvidia_provider import MultiNVIDIAProvider
from services.ai.nvidia_provider import NVIDIAProvider
from services.ai.provider import AIProvider

if TYPE_CHECKING:
    from services.ai.ai_service import AIService

logger = logging.getLogger(__name__)


def create_provider(
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> AIProvider:
    provider_name = (provider or AI_PROVIDER).strip().lower()

    if provider_name == "nvidia":
        if not api_key and NVIDIA_API_KEY_2:
            logger.info(
                "Creating multi-key NVIDIA provider (load-splitting) | model=%s",
                model or AI_MODEL or "default",
            )
            p1 = NVIDIAProvider(
                api_key=NVIDIA_API_KEY,
                base_url=base_url or NVIDIA_BASE_URL or None,
                model=model or AI_MODEL or None,
            )
            p2 = NVIDIAProvider(
                api_key=NVIDIA_API_KEY_2,
                base_url=base_url or NVIDIA_BASE_URL or None,
                model=model or AI_MODEL or None,
            )
            return MultiNVIDIAProvider(p1, p2)

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


def create_ai_service() -> AIService:
    from services.ai.ai_service import AIService

    provider = create_provider()
    return AIService(provider)


_shared_provider: AIProvider | None = None
_shared_provider_lock = threading.Lock()


def get_shared_provider() -> AIProvider:
    """Process-wide singleton AIProvider, created once and reused by every
    caller instead of each independently calling create_provider().

    Each NVIDIAProvider carries its own proactive rate limiter (see
    nvidia_provider.py) -- that only actually throttles the real aggregate
    request rate if callers share one instance. Before this, OLLO (via
    api/main.py's one-time _ai_svc) and services/telegram/bot.py's
    get_ollo_service() already did this correctly by accident, but
    market/intelligence/news.py's classify_sentiment()/classify_and_score()
    called create_provider() fresh on every single invocation -- a brand
    new provider, and therefore a brand new full token bucket, every call.
    That defeated the rate limiter entirely for the single heaviest AI
    consumer in the app (news classification runs once per symbol per scan,
    plus on-demand from council/news_agent.py's live NewsAgent path, plus
    the periodic Telegram news job) and meant this one path had zero
    coordination with every other AI consumer hitting the same NVIDIA
    key(s). This makes that coordination real: one shared instance, one
    real rate limit, across all of OLLO/council/news/Telegram.
    """
    global _shared_provider
    if _shared_provider is None:
        with _shared_provider_lock:
            if _shared_provider is None:
                _shared_provider = create_provider()
    return _shared_provider
