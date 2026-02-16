from dataclasses import dataclass, field
from difflib import SequenceMatcher
from app.path_ai.core.config import settings
from app.path_ai.monitoring.logger import get_logger

logger = get_logger(__name__)

CONFUSION_KEYWORDS = [
    "bingung", "tidak paham", "gak ngerti", "ga ngerti", "nggak ngerti",
    "masih belum", "tetap tidak", "masih bingung", "belum mengerti",
    "kurang paham", "susah", "sulit", "gimana sih",
    "tolong jelaskan lagi", "ulangi", "jelaskan lagi",
]

def _is_confused(message: str) -> bool:
    return any(kw in message.lower() for kw in CONFUSION_KEYWORDS)

def _context_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().split(), b.lower().split()).ratio()


@dataclass
class EscalationContext:
    student_id: str = ""
    topic: str = ""
    interaction_count: int = 0
    confusion_history: list[str] = field(default_factory=list)
    ai_failure_count: int = 0
    manual_flag: bool = False
    similarity_threshold: float = 0.4
    max_confusion_repeats: int = 3

    def record_message(self, message: str) -> None:
        self.interaction_count += 1
        if _is_confused(message):
            self.confusion_history.append(message)

    def record_ai_failure(self) -> None:
        self.ai_failure_count += 1

    def request_teacher(self) -> None:
        self.manual_flag = True


class EscalationEngine:

    def __init__(self, max_confusion: int | None = None):
        self.max_confusion = max_confusion or settings.escalation_max_failures

    def _count_similar_confusions(self, ctx: EscalationContext) -> int:
        history = ctx.confusion_history
        if len(history) < 2: return len(history)
        latest = history[-1]
        return 1 + sum(
            1 for prev in history[:-1]
            if _context_similarity(prev, latest) >= ctx.similarity_threshold
        )

    def should_escalate(self, ctx: EscalationContext) -> bool:
        if ctx.manual_flag: return True                            # Trigger 1
        if ctx.ai_failure_count >= 1: return True                  # Trigger 2
        if len(ctx.confusion_history) >= 2:                        # Trigger 3
            if self._count_similar_confusions(ctx) >= self.max_confusion:
                return True
        return False

    def get_escalation_reason(self, ctx: EscalationContext) -> str:
        reasons = []
        if ctx.manual_flag:
            reasons.append("Siswa meminta bantuan guru")
        if ctx.ai_failure_count >= 1:
            reasons.append(f"AI tidak membantu ({ctx.ai_failure_count}x)")
        if len(ctx.confusion_history) >= 2:
            n = self._count_similar_confusions(ctx)
            if n >= self.max_confusion:
                reasons.append(f"Siswa kebingungan {n}x pada konteks serupa")
        return " | ".join(reasons) or "Tidak ada alasan"
