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
    AIProvider,
    AIService,
    ConversationMemory,
    GenerationResult,
    HealthStatus,
    InMemoryConversation,
    InMemorySessionMemory,
    Message,
    NVIDIAProvider,
    briefing_prompt,
    council_prompt,
    create_ai_service,
    create_provider,
    explain_prompt,
    ollo_prompt,
    scanner_prompt,
)


def _make_request() -> httpx.Request:
    return httpx.Request("POST", "http://test.nvidia.com/v1/chat/completions")


def _make_response(
    status_code: int = 200,
    json_data: dict | None = None,
    headers: dict | None = None,
) -> httpx.Response:
    req = _make_request()
    return httpx.Response(status_code, json=json_data or {}, request=req, headers=headers or {})


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
        assert provider.model == "meta/llama-3.3-70b-instruct"

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

    def test_generate_retries_on_429_then_succeeds(self, monkeypatch):
        """429 (rate limited) must be retried, unlike other 4xx codes --
        it's the server explicitly telling us to back off and try again."""
        monkeypatch.setattr("services.ai.nvidia_provider.time.sleep", lambda *_: None)
        provider = NVIDIAProvider(api_key="test-key")
        call_count = [0]

        def mock_post(self, url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return _make_response(429, json_data={"error": "rate limited"})
            return _make_response(
                200,
                json_data={
                    "id": "cmpl-6",
                    "choices": [{"message": {"content": "recovered after 429"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                    "model": "meta/llama-3.3-70b-instruct",
                },
            )

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        result = provider.generate("hi")
        assert call_count[0] == 2
        assert result.content == "recovered after 429"
        assert result.retries == 1

    def test_generate_429_exhausts_all_retries(self, monkeypatch):
        monkeypatch.setattr("services.ai.nvidia_provider.time.sleep", lambda *_: None)
        provider = NVIDIAProvider(api_key="test-key")
        call_count = [0]

        def mock_post(self, url, **kwargs):
            call_count[0] += 1
            return _make_response(429, json_data={"error": "rate limited"})

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        result = provider.generate("hi")
        assert call_count[0] == 3
        assert result.content == ""
        assert result.error is not None

    def test_generate_401_still_fails_fast_no_retry(self, monkeypatch):
        """Non-retryable 4xx codes (bad key, malformed request, unknown
        model) must NOT be retried -- retrying can't fix them, only wastes
        the request's time budget."""
        provider = NVIDIAProvider(api_key="bad-key")
        call_count = [0]

        def mock_post(self, url, **kwargs):
            call_count[0] += 1
            return _make_response(401, json_data={"error": "unauthorized"})

        monkeypatch.setattr(httpx.Client, "post", mock_post)
        result = provider.generate("test")
        assert call_count[0] == 1
        assert result.content == ""

    def test_retry_delay_honors_retry_after_header(self):
        resp = _make_response(429, headers={"Retry-After": "5"})
        error = httpx.HTTPStatusError("HTTP 429", request=resp.request, response=resp)
        assert NVIDIAProvider._retry_delay_seconds(0, error) == 5.0

    def test_retry_delay_caps_retry_after(self):
        resp = _make_response(429, headers={"Retry-After": "9999"})
        error = httpx.HTTPStatusError("HTTP 429", request=resp.request, response=resp)
        assert NVIDIAProvider._retry_delay_seconds(0, error) == 30.0

    def test_retry_delay_falls_back_to_backoff_without_header(self):
        resp = _make_response(429)
        error = httpx.HTTPStatusError("HTTP 429", request=resp.request, response=resp)
        assert NVIDIAProvider._retry_delay_seconds(0, error) == 1.0
        assert NVIDIAProvider._retry_delay_seconds(1, error) == 2.0

    def test_retry_delay_uses_backoff_for_non_429(self):
        timeout_error = httpx.TimeoutException("timeout", request=_make_request())
        assert NVIDIAProvider._retry_delay_seconds(0, timeout_error) == 1.0


class TestProviderFactory:
    """Provider factory creates correct provider instances."""

    def test_create_nvidia_provider(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "nvidia")
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        provider = create_provider()
        assert isinstance(provider, NVIDIAProvider)

    def test_create_nvidia_provider_multi_key(self, monkeypatch):
        from services.ai.multi_nvidia_provider import MultiNVIDIAProvider
        monkeypatch.setattr("config.AI_PROVIDER", "nvidia")
        monkeypatch.setattr("config.NVIDIA_API_KEY", "first-key")
        monkeypatch.setattr("config.NVIDIA_API_KEY_2", "second-key")

        provider = create_provider()
        assert isinstance(provider, MultiNVIDIAProvider)
        assert len(provider._providers) == 2
        assert provider._providers[0]._api_key == "first-key"
        assert provider._providers[1]._api_key == "second-key"

    def test_create_nvidia_provider_multi_key_fallback_empty(self, monkeypatch):
        monkeypatch.setattr("config.AI_PROVIDER", "nvidia")
        monkeypatch.setattr("config.NVIDIA_API_KEY", "first-key")
        monkeypatch.setattr("config.NVIDIA_API_KEY_2", "")

        provider = create_provider()
        assert isinstance(provider, NVIDIAProvider)
        assert provider._api_key == "first-key"

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


class TestMultiNVIDIAProvider:
    """Unit tests for MultiNVIDIAProvider."""

    def test_round_robin_alternation(self):
        from unittest.mock import MagicMock

        from services.ai.multi_nvidia_provider import MultiNVIDIAProvider
        from services.ai.provider import GenerationResult

        p1 = MagicMock()
        p2 = MagicMock()

        p1.model = "test-model"
        p2.model = "test-model"

        p1.generate.return_value = GenerationResult(
            content="p1 response",
            model="test-model",
            provider="nvidia",
            duration_ms=10.0,
        )
        p2.generate.return_value = GenerationResult(
            content="p2 response",
            model="test-model",
            provider="nvidia",
            duration_ms=12.0,
        )

        multi = MultiNVIDIAProvider(p1, p2)

        # Call 1: should go to p1
        res1 = multi.generate("test")
        assert res1.content == "p1 response"
        p1.generate.assert_called_once_with("test")
        p2.generate.assert_not_called()

        p1.reset_mock()
        p2.reset_mock()

        # Call 2: should go to p2
        res2 = multi.generate("test")
        assert res2.content == "p2 response"
        p2.generate.assert_called_once_with("test")
        p1.generate.assert_not_called()

        p1.reset_mock()
        p2.reset_mock()

        # Call 3: should go back to p1
        res3 = multi.generate("test")
        assert res3.content == "p1 response"
        p1.generate.assert_called_once_with("test")
        p2.generate.assert_not_called()

    def test_round_robin_chat_alternation(self):
        from unittest.mock import MagicMock

        from services.ai.multi_nvidia_provider import MultiNVIDIAProvider
        from services.ai.provider import GenerationResult

        p1 = MagicMock()
        p2 = MagicMock()
        p1.model = "test-model"

        p1.chat.return_value = GenerationResult(
            content="p1 chat response",
            model="test-model",
            provider="nvidia",
            duration_ms=10.0,
        )
        p2.chat.return_value = GenerationResult(
            content="p2 chat response",
            model="test-model",
            provider="nvidia",
            duration_ms=12.0,
        )

        multi = MultiNVIDIAProvider(p1, p2)
        messages = [{"role": "user", "content": "hello"}]

        # Call 1: p1
        res1 = multi.chat(messages)
        assert res1.content == "p1 chat response"
        p1.chat.assert_called_once_with(messages)
        p2.chat.assert_not_called()

        p1.reset_mock()
        p2.reset_mock()

        # Call 2: p2
        res2 = multi.chat(messages)
        assert res2.content == "p2 chat response"
        p2.chat.assert_called_once_with(messages)
        p1.chat.assert_not_called()

    def test_failover_on_error(self):
        from unittest.mock import MagicMock

        from services.ai.multi_nvidia_provider import MultiNVIDIAProvider
        from services.ai.provider import GenerationResult

        p1 = MagicMock()
        p2 = MagicMock()
        p1.model = "test-model"

        # First call goes to p1, which fails. It should fall back to p2, which succeeds.
        p1.generate.return_value = GenerationResult(
            content="",
            model="test-model",
            provider="nvidia",
            duration_ms=100.0,
            error="Rate limit exceeded (429)",
        )
        p2.generate.return_value = GenerationResult(
            content="p2 recovery response",
            model="test-model",
            provider="nvidia",
            duration_ms=10.0,
        )

        multi = MultiNVIDIAProvider(p1, p2)
        res = multi.generate("test prompt")

        # Verify both were called (p1 first, then p2)
        p1.generate.assert_called_once_with("test prompt")
        p2.generate.assert_called_once_with("test prompt")
        assert res.content == "p2 recovery response"
        assert res.error is None

    def test_health_scenarios(self):
        from unittest.mock import MagicMock

        from services.ai.multi_nvidia_provider import MultiNVIDIAProvider
        from services.ai.provider import HealthStatus

        p1 = MagicMock()
        p2 = MagicMock()
        p1.model = "test-model"

        multi = MultiNVIDIAProvider(p1, p2)

        # Scenario 1: Both healthy
        p1.health.return_value = HealthStatus(connected=True, model="test-model", latency_ms=15.0, provider="nvidia")
        p2.health.return_value = HealthStatus(connected=True, model="test-model", latency_ms=25.0, provider="nvidia")

        h_ok = multi.health()
        assert h_ok.connected is True
        assert h_ok.latency_ms == 25.0  # max of 15 and 25
        assert h_ok.error is None

        # Scenario 2: One healthy, one failed
        p1.health.return_value = HealthStatus(connected=True, model="test-model", latency_ms=15.0, provider="nvidia")
        p2.health.return_value = HealthStatus(
            connected=False, model="test-model", latency_ms=25.0, provider="nvidia", error="HTTP 401 Unauthorized"
        )

        h_deg = multi.health()
        assert h_deg.connected is False
        assert h_deg.latency_ms == 25.0
        assert "Key 2: HTTP 401 Unauthorized" in h_deg.error

        # Scenario 3: Both failed
        p1.health.return_value = HealthStatus(
            connected=False, model="test-model", latency_ms=5.0, provider="nvidia", error="HTTP 429"
        )
        p2.health.return_value = HealthStatus(
            connected=False, model="test-model", latency_ms=10.0, provider="nvidia", error="HTTP 500"
        )

        h_fail = multi.health()
        assert h_fail.connected is False
        assert "Key 1: HTTP 429" in h_fail.error
        assert "Key 2: HTTP 500" in h_fail.error

    def test_close(self):
        from unittest.mock import MagicMock

        from services.ai.multi_nvidia_provider import MultiNVIDIAProvider

        p1 = MagicMock()
        p2 = MagicMock()

        multi = MultiNVIDIAProvider(p1, p2)
        multi.close()

        p1.close.assert_called_once()
        p2.close.assert_called_once()
