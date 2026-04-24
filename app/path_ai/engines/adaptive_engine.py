from app.path_ai.schemas.quiz_schema import (
    DiagnosticSignal, DiagnosticResult, DiagnosticAnswer,
)
from app.path_ai.monitoring.logger import get_logger

logger = get_logger(__name__)


class AdaptiveEngine:

    def __init__(self, green_threshold: float = 0.6):
        self.green_threshold = green_threshold

    def classify_diagnostic(
        self,
        answers: list[DiagnosticAnswer],
        student_id: str = "",
    ) -> DiagnosticResult:
        if not answers:
            return DiagnosticResult(
                student_id=student_id, signal=DiagnosticSignal.YELLOW,
                correct_count=0, total_count=0,
                weak_concepts=[], recommended_path="support",
            )

        correct_count = sum(1 for a in answers if a.is_correct)
        total_count = len(answers)
        ratio = correct_count / total_count

        signal = (
            DiagnosticSignal.GREEN if ratio >= self.green_threshold
            else DiagnosticSignal.YELLOW
        )

        weak_concepts = list(set(
            a.concept_tag for a in answers
            if not a.is_correct and a.concept_tag
        ))

        recommended_path = "fast-track" if signal == DiagnosticSignal.GREEN else "support"

        result = DiagnosticResult(
            student_id=student_id, signal=signal, answers=answers,
            correct_count=correct_count, total_count=total_count,
            weak_concepts=weak_concepts, recommended_path=recommended_path,
        )

        logger.info("Diagnostic classified", student_id=student_id,
            signal=signal.value, score=f"{correct_count}/{total_count}")
        return result