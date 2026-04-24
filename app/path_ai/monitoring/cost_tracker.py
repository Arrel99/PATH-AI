from dataclasses import dataclass
from collections import defaultdict
from app.path_ai.core.config import settings
from app.path_ai.monitoring.token_tracker import TokenUsage, get_tracker
from app.path_ai.monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CostEntry:
    task: str
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    prompt_tokens: int
    completion_tokens: int


class CostTracker:
    def __init__(self, input_cost_per_million=None, output_cost_per_million=None):
        self._input_cpm = settings.input_cost_per_million if input_cost_per_million is None else input_cost_per_million
        self._output_cpm = settings.output_cost_per_million if output_cost_per_million is None else output_cost_per_million
        self._history: list[CostEntry] = []
        self._by_task: dict[str, float] = defaultdict(float)
        self._total_cost: float = 0.0

    def calculate_cost(self, usage: TokenUsage) -> tuple[float, float, float]:
        input_cost = (usage.prompt_tokens / 1_000_000) * self._input_cpm
        output_cost = (usage.completion_tokens / 1_000_000) * self._output_cpm
        return round(input_cost, 6), round(output_cost, 6), round(input_cost + output_cost, 6)

    def record(self, usage: TokenUsage) -> CostEntry:
        """Calculate and store cost for a single LLM call."""
        input_cost, output_cost, total_cost = self.calculate_cost(usage)
        entry = CostEntry(
            task=usage.task,
            input_cost_usd=input_cost,
            output_cost_usd=output_cost,
            total_cost_usd=total_cost,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
        )
        self._history.append(entry)
        self._by_task[usage.task] += total_cost
        self._total_cost += total_cost
        return entry

    def get_summary(self) -> dict:
        return {
            "total_cost_usd": round(self._total_cost, 6),
            "by_task": dict(self._by_task),
            "total_calls": len(self._history),
            "model_pricing": {
                "input_per_million": self._input_cpm,
                "output_per_million": self._output_cpm,
            },
        }


_cost_tracker = CostTracker()

def get_cost_tracker() -> CostTracker:
    return _cost_tracker