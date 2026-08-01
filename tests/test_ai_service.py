"""Tests for AI Service foundation layer.

Verifies:
  - AIProvider abstract interface can be implemented
  - NVIDIAProvider generate/chat return GenerationResult
  - NVIDIAProvider health returns HealthStatus
  - NVIDIAProvider handles errors gracefully (timeout, auth failure)
  - AIService delegates correctly to provider
  - Provider matching regex: all GenerationResult / HealthStatus fields populated
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from services.ai import (
    AIService,
    AIProvider,
    GenerationResult,
    HealthStatus,
    NVIDIAProvider,
    create_provider,
    create_ai_service,
    briefing_prompt,
    council_prompt,
    explain_prompt,
    ollo_prompt,
    scanner_prompt,
    ConversationMemory,
    InMemoryConversation,
    Message,
    SessionMemory,
    InMemorySessionMemory,
)


def _make_request() -> httpx.Request:
    return httpx.Request("POST", "http://test.nvidia.com/v1/chat/completions")


def _make_response(
    status_code: int = 200,
    json_data: dict | None = None,
) -> httpx.Response:
    req = _make_request()
    return httpx.Response(status_code, json=json_data or {}, request=req)


class AlwaysOkProvider(AIProvider):
    """Test provider that always succeeds."""

    @property
    def model(self) -> str:
        return "test-model"

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        return GenerationResult(
            content=f"generated: {prompt}",
            model="test-model",
            provider="test",
            duration_ms=10.0,
            tokens_in=5,
            tokens_out=10,
        )

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> GenerationResult:
        return GenerationResult(
            content=f"chat: {messages[-1]['content']}",
            model="test-model",
            provider="test",
            duration_ms=10.0,
            tokens_in=5,
            tokens_out=10,
        )

    def health(self) -> HealthStatus:
        return HealthStatus(
            connected=True,
            model="test-model",
            latency_ms=5.0,
            provider="test",
        )


class TestAIProvider:
    """Abstract provider can be implemented."""

    def test_provider_interface(self):
        provider = AlwaysOkProvider()
        assert provider.model == "test-model"

    def test_generate(self):
        provider = AlwaysOkProvider()
        result = provider.generate("hello")
        assert isinstance(result, GenerationResult)
        assert result.content == "generated: hello"
        assert result.provider == "test"
        assert result.model == "test-model"

    def test_chat(self):
        provider = AlwaysOkProvider()
        result = provider.chat([{"role": "user", "content": "hi"}])
        assert isinstance(result, GenerationResult)
        assert result.content == "chat: hi"

    def test_health(self):
        provider = AlwaysOkProvider()
        status = provider.health()
        assert isinstance(status, HealthStatus)
        assert status.connected is True
        assert status.provider == "test"


class TestAIService:
    """AIService delegates correctly to provider."""

    def test_generate_delegates(self):
        provider = AlwaysOkProvider()
        svc = AIService(provider)
        result = svc.generate("hello")
        assert result.content == "generated: hello"

    def test_chat_delegates(self):
        provider = AlwaysOkProvider()
        svc = AIService(provider)
        result = svc.chat([{"role": "user", "content": "hi"}])
        assert result.content == "chat: hi"

    def test_health_delegates(self):
        provider = AlwaysOkProvider()
        svc = AIService(provider)
        status = svc.health()
        assert status.connected is True

    def test_model_property(self):
        provider = AlwaysOkProvider()
        svc = AIService(provider)
        assert svc.model == "test-model"

    def test_provider_property(self):
        provider = AlwaysOkProvider()
        svc = AIService(provider)
        assert svc.provider is provider


class TestNVIDIAProvider:
    """NVIDIAProvider unit tests with mocked HTTP."""

    def test_generate_success(self, monkeypatch):
        provider = NVIDIAProvider(api_key="test-key")

        def mock_post(self, url, **kwargs):
            return _make_response(
                200,
                json_data={
                    "id": "cmpl-1",
                    "choices": [{"message": {"content": "Hello from NVIDIA"}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20},
                    "model": "meta/llama3-70b-instruct",
                },
            )

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        result = provider.generate("test prompt")
        assert result.content == "Hello from NVIDIA"
        assert result.provider == "nvidia"
        assert result.tokens_in == 10
        assert result.tokens_out == 20
        assert result.error is None

    def test_chat_success(self, monkeypatch):
        provider = NVIDIAProvider(api_key="test-key")

        def mock_post(self, url, **kwargs):
            return _make_response(
                200,
                json_data={
                    "id": "cmpl-2",
                    "choices": [{"message": {"content": "Chat response"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 15},
                    "model": "meta/llama3-70b-instruct",
                },
            )

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        result = provider.chat([{"role": "user", "content": "hi"}])
        assert result.content == "Chat response"
        assert result.error is None

    def test_health_success(self, monkeypatch):
        provider = NVIDIAProvider(api_key="test-key")

        def mock_post(self, url, **kwargs):
            return _make_response(
                200,
                json_data={
                    "id": "cmpl-ping",
                    "choices": [{"message": {"content": "ok"}}],
                    "usage": {},
                    "model": "meta/llama3-70b-instruct",
                },
            )

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        status = provider.health()
        assert status.connected is True
        assert status.provider == "nvidia"
        assert status.error is None

    def test_generate_http_error(self, monkeypatch):
        provider = NVIDIAProvider(api_key="bad-key")

        def mock_post(self, url, **kwargs):
            return _make_response(401, json_data={"error": "unauthorized"})

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        result = provider.generate("test")
        assert result.content == ""
        assert result.error is not None

    def test_generate_timeout(self, monkeypatch):
        provider = NVIDIAProvider(api_key="test-key")

        def mock_post(self, url, **kwargs):
            raise httpx.TimeoutException("timeout", request=_make_request())

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        result = provider.generate("test")
        assert result.content == ""
        assert result.error is not None

    def test_generate_retry_then_succeed(self, monkeypatch):
        provider = NVIDIAProvider(api_key="test-key")
        call_count = [0]

        def mock_post(self, url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.TimeoutException("timeout", request=_make_request())
            return _make_response(
                200,
                json_data={
                    "id": "cmpl-3",
                    "choices": [{"message": {"content": "Retry success"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 10},
                    "model": "meta/llama3-70b-instruct",
                },
            )

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        result = provider.generate("test")
        assert result.content == "Retry success"
        assert result.error is None
        assert call_count[0] == 2

    def test_model_property(self):
        provider = NVIDIAProvider(api_key="test-key", model="custom-model")
        assert provider.model == "custom-model"

    def test_default_model(self):
        provider = NVIDIAProvider(api_key="test-key")
        assert provider.model == "meta/llama3-70b-instruct"

    def test_close(self):
        provider = NVIDIAProvider(api_key="test-key")
        provider.close()

    def test_retries_on_success(self, monkeypatch):
        provider = NVIDIAProvider(api_key="test-key")

        def mock_post(self, url, **kwargs):
            return _make_response(
                200,
                json_data={
                    "id": "cmpl-4",
                    "choices": [{"message": {"content": "ok"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                    "model": "meta/llama3-70b-instruct",
                },
            )

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        result = provider.generate("hi")
        assert result.retries == 0

    def test_retries_after_failure(self, monkeypatch):
        provider = NVIDIAProvider(api_key="test-key")
        call_count = [0]

        def mock_post(self, url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.TimeoutException("timeout", request=_make_request())
            return _make_response(
                200,
                json_data={
                    "id": "cmpl-5",
                    "choices": [{"message": {"content": "recovered"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                    "model": "meta/llama3-70b-instruct",
                },
            )

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        result = provider.generate("hi")
        assert result.retries == 1
        assert result.content == "recovered"


class TestProviderFactory:
    """Provider factory creates correct provider instances."""

    def test_create_nvidia_provider(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "nvidia")
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        provider = create_provider()
        assert isinstance(provider, NVIDIAProvider)

    def test_create_nvidia_provider_explicit(self):
        provider = create_provider(provider="nvidia", api_key="test-key")
        assert isinstance(provider, NVIDIAProvider)

    def test_create_openai_raises(self):
        with pytest.raises(NotImplementedError):
            create_provider(provider="openai")

    def test_create_ollama_raises(self):
        with pytest.raises(NotImplementedError):
            create_provider(provider="ollama")

    def test_create_local_raises(self):
        with pytest.raises(NotImplementedError):
            create_provider(provider="local")

    def test_create_unknown_raises(self):
        with pytest.raises(ValueError):
            create_provider(provider="foobar")

    def test_create_ai_service(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "nvidia")
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        svc = create_ai_service()
        assert isinstance(svc, AIService)
        assert isinstance(svc.provider, NVIDIAProvider)


class TestPromptLibrary:
    """All prompt library functions return strings."""

    def test_briefing_prompt(self):
        result = briefing_prompt("Market trending up", "Portfolio at 80%")
        assert isinstance(result, str)
        assert "Market Summary" in result
        assert "Market trending up" in result
        assert "Portfolio at 80%" in result

    def test_explain_prompt(self):
        result = explain_prompt(
            symbol="BTCUSDT",
            side="LONG",
            score_breakdown="Trend: 0.9, Volume: 0.8",
            risk_context="ATR: 500, Volatility: NORMAL",
            market_regime="BULLISH",
        )
        assert isinstance(result, str)
        assert "BTCUSDT" in result
        assert "LONG" in result

    def test_council_prompt(self):
        result = council_prompt(
            topic="Should we open BTC long?",
            context="BTC at 50k, trending up",
            agent_roles=["Risk Analyst", "Technical Analyst"],
        )
        assert isinstance(result, str)
        assert "Risk Analyst" in result
        assert "Technical Analyst" in result

    def test_ollo_prompt(self):
        result = ollo_prompt("What is the market doing?")
        assert isinstance(result, str)
        assert "OLLO" in result

    def test_ollo_prompt_with_history(self):
        result = ollo_prompt("What is BTC at?", conversation_history="User asked about ETH earlier.")
        assert isinstance(result, str)
        assert "Previous conversation" in result

    def test_scanner_prompt(self):
        result = scanner_prompt(
            symbol="ETHUSDT",
            technical_signals="RSI: 55, MACD: bullish",
            volume_analysis="Volume above average",
            market_context="BTC bullish",
        )
        assert isinstance(result, str)
        assert "ETHUSDT" in result


class TestConversationMemory:
    """Conversation memory abstraction works."""

    def test_message_dataclass(self):
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_in_memory_add_and_get(self):
        mem = InMemoryConversation()
        mem.add_message("user", "hello")
        mem.add_message("assistant", "hi there")
        history = mem.get_history()
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].content == "hi there"

    def test_in_memory_clear(self):
        mem = InMemoryConversation()
        mem.add_message("user", "hello")
        mem.clear()
        assert len(mem.get_history()) == 0

    def test_context_window_property(self):
        mem = InMemoryConversation(context_window=2048)
        assert mem.context_window == 2048
        mem.context_window = 4096
        assert mem.context_window == 4096

    def test_in_memory_trim_respects_window(self):
        mem = InMemoryConversation(context_window=10)
        for i in range(20):
            mem.add_message("user", "word " * 5)
        assert len(mem.get_history()) < 20

    def test_session_memory_create_and_get(self):
        sm = InMemorySessionMemory()
        conv = sm.create_session("test-1")
        assert isinstance(conv, ConversationMemory)
        assert sm.get_session("test-1") is conv

    def test_session_memory_delete(self):
        sm = InMemorySessionMemory()
        sm.create_session("test-1")
        sm.delete_session("test-1")
        assert sm.get_session("test-1") is None

    def test_session_memory_missing(self):
        sm = InMemorySessionMemory()
        assert sm.get_session("nonexistent") is None
