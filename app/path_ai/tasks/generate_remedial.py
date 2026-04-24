from app.path_ai.core.base_llm import BaseLLM
from app.path_ai.core.config import settings
from app.path_ai.prompts import remedial
from app.path_ai.schemas.grading_schema import RemedialTrigger
from app.path_ai.monitoring.logger import get_logger
from app.path_ai.monitoring.token_tracker import track_usage

logger = get_logger(__name__)


async def generate_remedial(
    llm: BaseLLM,
    remedial_trigger: RemedialTrigger,
    original_content: str = "",
    student_level: str = "SMA",
) -> tuple[str, dict]:
    if not remedial_trigger.needs_remedial:
        logger.info("No remedial needed, skipping")
        return "", {"skipped": True}

    logger.info("generate_remedial started",
                weak_concepts=remedial_trigger.weak_concepts)

    misconception_dicts = [m.model_dump() for m in remedial_trigger.misconceptions]

    messages = [
        {"role": "system", "content": remedial.get_system_prompt()},
        {"role": "user", "content": remedial.build_user_prompt(
            weak_concepts=remedial_trigger.weak_concepts,
            misconceptions=misconception_dicts,
            original_content=original_content,
            student_level=student_level,
        )},
    ]

    response = await llm.generate(
        messages=messages, temperature=settings.default_temperature,
    )

    usage_meta = track_usage(response, task="generate_remedial")

    return response.content, {
        "usage": usage_meta, "latency_ms": response.latency_ms,
        "weak_concepts": remedial_trigger.weak_concepts,
    }