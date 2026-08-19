from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

from config import DEEPSEEK_MAX_REQUESTS_PER_SECOND
from market.provider.rate_limiter import TokenBucketRateLimiter
from services.ai.provider import AIProvider, GenerationResult, HealthStatus

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://api.deepseek.com"
_DEFAULT_MODEL = "deepseek-v4-flash"
_DEFAULT_TIMEOUT = 60.0
_MAX_RETRIES = 3
_RETRY_DELAY = 1.0
_RETRY_AFTER_CAP_SECONDS = 30.0


class DeepSeekProvider(AIProvider):
    """OpenAI-compatible chat completions client for platform.deepseek.com.

    Structurally mirrors NVIDIAProvider (same retry/backoff/rate-limiting
    discipline, same GenerationResult/HealthStatus shape) rather than
    sharing a base class with it -- NVIDIAProvider is live, load-bearing
    infrastructure for the real trading pipeline; a shared abstraction
    wasn't worth the risk of touching it to add a second provider.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        requests_per_second: float = DEEPSEEK_MAX_REQUESTS_PER_SECOND,
    ) -> None:
        self._api_key = api_key or ""
        self._base_url = (base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._model_name = model or _DEFAULT_MODEL
        self._timeout = timeout
        self._client = httpx.Client(timeout=httpx.Timeout(timeout))
        self._limiter = TokenBucketRateLimiter(requests_per_second)

    @property
    def model(self) -> str:
        return self._model_name

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        messages = [{"role": "user", "content": prompt}]
        return self._chat_completion(messages, **kwargs)

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> GenerationResult:
        return self._chat_completion(messages, **kwargs)

    def health(self) -> HealthStatus:
        start = time.perf_counter()
        try:
            self._check()
            elapsed = (time.perf_counter() - start) * 1000
            return HealthStatus(
                connected=True,
                model=self._model_name,
                latency_ms=round(elapsed, 2),
                provider="deepseek",
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("Health check failed: %s", e)
            return HealthStatus(
                connected=False,
                model=self._model_name,
                latency_ms=round(elapsed, 2),
                provider="deepseek",
                error=str(e),
            )

    def close(self) -> None:
        self._client.close()

    @staticmethod
    def _retry_delay_seconds(attempt: int, error: Exception | None) -> float:
        if isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 429:
            retry_after = error.response.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    return min(float(retry_after), _RETRY_AFTER_CAP_SECONDS)
                except ValueError:
                    pass
        return _RETRY_DELAY * (attempt + 1)

    def _chat_completion(self, messages: list[dict[str, Any]], **kwargs: Any) -> GenerationResult:
        self._limiter.acquire()

        start = time.perf_counter()
        last_error: Exception | None = None
        total_attempts = 0

        for attempt in range(_MAX_RETRIES):
            total_attempts = attempt + 1
            try:
                payload = {
                    "model": self._model_name,
                    "messages": messages,
                    # V4 models default to "thinking" mode (returns a
                    # reasoning_content trace, default effort high) unless
                    # explicitly disabled -- confirmed via DeepSeek's own
                    # API docs. Our only use case here is short news-
                    # sentiment classification, which needs no reasoning
                    # trace at all; leaving the default on would silently
                    # inflate output tokens (cost) and latency for every
                    # call. kwargs comes last so a future caller can still
                    # override this explicitly if a real use case needs it.
                    "thinking": {"type": "disabled"},
                    **kwargs,
                }

                headers = {
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                }

                resp = self._client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )

                if resp.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )

                data = resp.json()
                elapsed = (time.perf_counter() - start) * 1000
                content = data["choices"][0]["message"]["content"]

                usage = data.get("usage", {})
                tokens_in = usage.get("prompt_tokens")
                tokens_out = usage.get("completion_tokens")

                success_attempts = total_attempts - 1
                logger.info(
                    "DeepSeek success | model=%s | duration_ms=%s | tokens_in=%s | tokens_out=%s | retries=%s",
                    self._model_name, round(elapsed, 2), tokens_in, tokens_out, success_attempts,
                )

                return GenerationResult(
                    content=content,
                    model=self._model_name,
                    provider="deepseek",
                    duration_ms=round(elapsed, 2),
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    retries=success_attempts,
                )

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning("DeepSeek timeout (attempt %s/%s): %s", attempt + 1, _MAX_RETRIES, e)
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning("DeepSeek HTTP error (attempt %s/%s): %s", attempt + 1, _MAX_RETRIES, e)
                if e.response.status_code != 429 and 400 <= e.response.status_code < 500:
                    break
            except Exception as e:
                last_error = e
                logger.error("DeepSeek unexpected error (attempt %s/%s): %s", attempt + 1, _MAX_RETRIES, e)
                break

            if attempt < _MAX_RETRIES - 1:
                time.sleep(self._retry_delay_seconds(attempt, last_error))

        elapsed = (time.perf_counter() - start) * 1000
        logger.error("DeepSeek failed after %s attempts: %s", _MAX_RETRIES, last_error)
        return GenerationResult(
            content="",
            model=self._model_name,
            provider="deepseek",
            duration_ms=round(elapsed, 2),
            retries=_MAX_RETRIES,
            error=str(last_error) if last_error else "Unknown error",
        )

    def _check(self) -> None:
        self._limiter.acquire()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
        }
        resp = self._client.post(
            f"{self._base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        if resp.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {resp.status_code}",
                request=resp.request,
                response=resp,
            )
