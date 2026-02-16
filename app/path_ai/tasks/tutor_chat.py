from app.path_ai.core.base_llm import BaseLLM
from app.path_ai.core.config import settings
from app.path_ai.prompts import chat_tutor
from app.path_ai.engines.escalation_engine import EscalationEngine, EscalationContext
from app.path_ai.monitoring.logger import get_logger
from app.path_ai.monitoring.token_tracker import track_usage

logger = get_logger(__name__)


async def tutor_chat(
    llm: BaseLLM,
    student_message: str,
    conversation_history: list[dict] | None = None,
    context_material: str = "",
    subject: str = "",
    topic: str = "",
    escalation_context: EscalationContext | None = None,
) -> dict:
    logger.info(
        "tutor_chat started",
        subject=subject,
        topic=topic,
        history_length=len(conversation_history or []),
    )

    # Cek Eskalasi sebelum konteks
    escalation_engine = EscalationEngine()
    if escalation_context and escalation_engine.should_escalate(escalation_context):
        reason = escalation_engine.get_escalation_reason(escalation_context)
        logger.info("Escalation triggered BEFORE response", reason=reason)
        return {
            "response": (
                "Sepertinya kamu butuh penjelasan lebih lanjut dari guru. "
                "Saya akan menghubungkan kamu dengan guru untuk topik ini. "
            ),
            "should_escalate": True,
            "escalation_reason": reason,
            "metadata": {"escalated_before_response": True},
        }

    # Build chat
    messages = [
        {"role": "system", "content": chat_tutor.get_system_prompt(
            subject=subject,
            topic=topic,
        )},
        {"role": "user", "content": chat_tutor.build_user_prompt(
            student_message=student_message,
            conversation_history=conversation_history,
            context_material=context_material,
        )},
    ]

    response = await llm.generate(
        messages=messages,
        temperature=settings.default_temperature,
    )

    usage_meta = track_usage(response, task="tutor_chat")

    # Update Eskalasi setelah konteks
    should_escalate = False
    escalation_reason = ""
    if escalation_context:
        # Update context + deteksi siswa mumet
        escalation_context.record_message(student_message)
        if escalation_engine.should_escalate(escalation_context):
            should_escalate = True
            escalation_reason = escalation_engine.get_escalation_reason(
                escalation_context
            )

    logger.info(
        "tutor_chat completed",
        should_escalate=should_escalate,
        response_length=len(response.content),
    )

    return {
        "response": response.content,
        "should_escalate": should_escalate,
        "escalation_reason": escalation_reason,
        "metadata": {
            "usage": usage_meta,
            "latency_ms": response.latency_ms,
        },
    }
