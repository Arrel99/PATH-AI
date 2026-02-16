import time
from typing import Any, Optional
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.path_ai.core.base_llm import BaseLLM, LLMResponse
from app.path_ai.core.config import settings
from app.path_ai.monitoring.logger import get_logger

logger = get_logger(__name__)


class OpenRouterError(Exception):
    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)

class RateLimitError(OpenRouterError):
    pass


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

    @retry(
        retry=retry_if_exception_type((RateLimitError, httpx.ReadTimeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        reraise=True,
    )
    async def generate(self, messages, temperature=0.7, max_tokens=None,
                       response_format=None, **kwargs) -> LLMResponse:
        start = time.perf_counter()
        payload = {"model": self._model, "messages": messages, "temperature": temperature}
        if max_tokens: payload["max_tokens"] = max_tokens
        if response_format: payload["response_format"] = response_format
        payload.update(kwargs)

        response = await self._client.post("/chat/completions", json=payload)
        latency_ms = (time.perf_counter() - start) * 1000

        if response.status_code == 429:
            raise RateLimitError("Rate limited", status_code=429)
        if response.status_code != 200:
            raise OpenRouterError(f"Status {response.status_code}", response.status_code)

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
