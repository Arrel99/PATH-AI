from dataclasses import dataclass
from collections import defaultdict
from app.path_ai.core.base_llm import LLMResponse

@dataclass
class TokenUsage:
    task: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str = ""

class TokenTracker:
    def __init__(self):
        self._history: list[TokenUsage] = []
        self._total = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}

    def record(self, response: LLMResponse, task: str = "unknown") -> TokenUsage:
        usage = TokenUsage(task=task, prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens, model=response.model)
        self._history.append(usage)
        self._total["total"] += usage.total_tokens
        self._total["calls"] += 1
        return usage

_tracker = TokenTracker()
def get_tracker(): return _tracker

def track_usage(response: LLMResponse, task: str = "unknown") -> dict:
    u = _tracker.record(response, task)
    return {"task": u.task, "prompt_tokens": u.prompt_tokens,
            "completion_tokens": u.completion_tokens,
            "total_tokens": u.total_tokens, "model": u.model}
