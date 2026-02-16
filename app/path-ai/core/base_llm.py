from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    raw_response: Optional[dict] = field(default=None, repr=False)


class BaseLLM(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
        **kwargs: Any,
    ) -> LLMResponse: ...

    @abstractmethod
    async def close(self) -> None: ...
