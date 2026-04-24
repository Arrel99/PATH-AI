import time
from typing import Any, Optional
import httpx
from tenacity import (
    retry_if_exception_type, stop_after_attempt,
    wait_exponential, AsyncRetrying,
)

from app.path_ai.core.base_llm import BaseLLM, LLMResponse
from app.path_ai.core.config import settings
from app.path_ai.monitoring.logger import get_logger

logger = get_logger(__name__)


def _log_retry(retry_state):
    """Log each retry attempt with wait time."""
    wait = retry_state.next_action.sleep if retry_state.next_action else 0
    logger.warning(
        f"Retry attempt {retry_state.attempt_number} – waiting {wait:.1f}s before next try…"
    )


class OpenRouterError(Exception):
    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)

class RateLimitError(OpenRouterError):
    """429 – Too Many Requests"""

class ServiceUnavailableError(OpenRouterError):
    """503 – Model temporarily unavailable"""


class OpenRouterClient(BaseLLM):

    def __init__(self, api_key=None, base_url=None, model=None, timeout=None):
        self._api_key = api_key or settings.openrouter_api_key
        self._base_url = (base_url or settings.openrouter_base_url).rstrip("/")
        self._model = model or settings.model_name
        self._timeout = timeout or settings.timeout

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://path-ai.app",
                "X-Title": "PATH AI V2.5",
            },
            timeout=httpx.Timeout(self._timeout, connect=10.0),
        )

    async def generate(self, messages, temperature=0.7, max_tokens=None,
                       response_format=None, **kwargs) -> LLMResponse:
        retrying = AsyncRetrying(
            retry=retry_if_exception_type(
                (RateLimitError, ServiceUnavailableError, httpx.ReadTimeout)
            ),
            stop=stop_after_attempt(settings.max_retries + 1),
            wait=wait_exponential(multiplier=3, min=5, max=60),
            reraise=True,
            before_sleep=_log_retry,
        )
        async for attempt in retrying:
            with attempt:
                return await self._do_generate(
                    messages, temperature, max_tokens, response_format, **kwargs
                )

    async def _do_generate(self, messages, temperature=0.7, max_tokens=None,
                           response_format=None, **kwargs) -> LLMResponse:
        start = time.perf_counter()
        payload = {"model": self._model, "messages": messages, "temperature": temperature}
        if max_tokens: payload["max_tokens"] = max_tokens
        if response_format: payload["response_format"] = response_format
        payload.update(kwargs)

        response = await self._client.post("/chat/completions", json=payload)
        latency_ms = (time.perf_counter() - start) * 1000

        if response.status_code == 429:
            logger.warning("Rate limited (429) – will retry with backoff…")
            raise RateLimitError("Rate limited", status_code=429)
        if response.status_code in (502, 503):
            body = response.text[:300]
            logger.warning("Service unavailable (%s) – will retry… %s",
                           response.status_code, body)
            raise ServiceUnavailableError(
                f"Service unavailable ({response.status_code})",
                response.status_code, body,
            )
        if response.status_code != 200:
            body = response.text[:500]
            logger.error("OpenRouter error %s: %s", response.status_code, body)
            raise OpenRouterError(
                f"Status {response.status_code}: {body}",
                response.status_code, body,
            )

        data = response.json()
        choice = data.get("choices", [{}])[0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice.get("message", {}).get("content", ""),
            model=data.get("model", self._model),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=round(latency_ms, 2),
            raw_response=data,
        )

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self): return self
    async def __aexit__(self, *a): await self.close()
