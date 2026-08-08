from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

from services.ai.provider import AIProvider, GenerationResult, HealthStatus

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
_DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"
_DEFAULT_TIMEOUT = 60.0
_MAX_RETRIES = 3
_RETRY_DELAY = 1.0
_RETRY_AFTER_CAP_SECONDS = 30.0


class NVIDIAProvider(AIProvider):

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key or ""
        self._base_url = (base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._model_name = model or _DEFAULT_MODEL
        self._timeout = timeout
        self._client = httpx.Client(timeout=httpx.Timeout(timeout))

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
                provider="nvidia",
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("Health check failed: %s", e)
            return HealthStatus(
                connected=False,
                model=self._model_name,
                latency_ms=round(elapsed, 2),
                provider="nvidia",
                error=str(e),
            )

    def close(self) -> None:
        self._client.close()

    @staticmethod
    def _retry_delay_seconds(attempt: int, error: Exception | None) -> float:
        """Backoff before the next retry -- honors the server's Retry-After
        header on a 429 when present, since that's a more accurate signal
        than our own generic exponential backoff. Capped to keep a single
        retry cycle from stalling a request for an unreasonable amount of
        time."""
        if isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 429:
            retry_after = error.response.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    return min(float(retry_after), _RETRY_AFTER_CAP_SECONDS)
                except ValueError:
                    pass
        return _RETRY_DELAY * (attempt + 1)

    def _chat_completion(self, messages: list[dict[str, Any]], **kwargs: Any) -> GenerationResult:
        start = time.perf_counter()
        last_error: Exception | None = None
        total_attempts = 0

        for attempt in range(_MAX_RETRIES):
            total_attempts = attempt + 1
            try:
                payload = {
                    "model": self._model_name,
                    "messages": messages,
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
                    "NVIDIA success | model=%s | duration_ms=%s | tokens_in=%s | tokens_out=%s | retries=%s",
                    self._model_name, round(elapsed, 2), tokens_in, tokens_out, success_attempts,
                )

                return GenerationResult(
                    content=content,
                    model=self._model_name,
                    provider="nvidia",
                    duration_ms=round(elapsed, 2),
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    retries=success_attempts,
                )

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning("NVIDIA timeout (attempt %s/%s): %s", attempt + 1, _MAX_RETRIES, e)
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning("NVIDIA HTTP error (attempt %s/%s): %s", attempt + 1, _MAX_RETRIES, e)
                # 429 (rate limited) is explicitly a "retry me" signal, unlike
                # other 4xx codes (bad key, malformed request, unknown model)
                # which won't succeed no matter how many times we retry.
                if e.response.status_code != 429 and 400 <= e.response.status_code < 500:
                    break
            except Exception as e:
                last_error = e
                logger.error("NVIDIA unexpected error (attempt %s/%s): %s", attempt + 1, _MAX_RETRIES, e)
                break

            if attempt < _MAX_RETRIES - 1:
                time.sleep(self._retry_delay_seconds(attempt, last_error))

        elapsed = (time.perf_counter() - start) * 1000
        logger.error("NVIDIA failed after %s attempts: %s", _MAX_RETRIES, last_error)
        return GenerationResult(
            content="",
            model=self._model_name,
            provider="nvidia",
            duration_ms=round(elapsed, 2),
            retries=_MAX_RETRIES,
            error=str(last_error) if last_error else "Unknown error",
        )

    def _check(self) -> None:
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
