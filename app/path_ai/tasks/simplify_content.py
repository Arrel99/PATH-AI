from app.path_ai.core.base_llm import BaseLLM
from app.path_ai.core.config import settings
from app.path_ai.prompts import simplifier
from app.path_ai.monitoring.logger import get_logger
from app.path_ai.monitoring.token_tracker import track_usage

logger = get_logger(__name__)


async def simplify_content(
    llm: BaseLLM,
    content: str,
    mode: str = "simplifier",
    target_level: str = "SMA",
    topic: str = "",
    weak_concepts: list[str] | None = None,
) -> tuple[str, dict]:
    logger.info(
        "simplify_content started",
        mode=mode,
        topic=topic,
        weak_concepts=weak_concepts,
    )

    messages = [
        {"role": "system", "content": simplifier.get_system_prompt()},
        {"role": "user", "content": simplifier.build_user_prompt(
            content=content,
            mode=mode,
            target_level=target_level,
            topic=topic,
            weak_concepts=weak_concepts,
        )},
    ]

    response = await llm.generate(
        messages=messages,
        temperature=settings.default_temperature,
    )

    usage_meta = track_usage(response, task="simplify_content")

    logger.info(
        "simplify_content completed",
        mode=mode,
        output_length=len(response.content),
    )

    return response.content, {"usage": usage_meta, "latency_ms": response.latency_ms}