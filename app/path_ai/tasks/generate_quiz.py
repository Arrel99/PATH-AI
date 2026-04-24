from app.path_ai.core.base_llm import BaseLLM, LLMResponse
from app.path_ai.core.config import settings
from app.path_ai.prompts import quiz_generator
from app.path_ai.schemas.quiz_schema import GeneratedQuiz
from app.path_ai.validation.llm_validator import full_validation_pipeline
from app.path_ai.monitoring.logger import get_logger
from app.path_ai.monitoring.token_tracker import track_usage

logger = get_logger(__name__)

async def generate_quiz(
    llm: BaseLLM,
    content: str,
    num_questions: int = 5,
    question_type: str = "multiple_choice",
    difficulty: str = "medium",
    topic: str = "",
    skip_llm_validation: bool = False,
) -> tuple[GeneratedQuiz | None, dict]:
    logger.info(
        "generate_quiz started",
        num_questions=num_questions,
        difficulty=difficulty,
        topic=topic,
    )

    # Build messages
    messages = [
        {"role": "system", "content": quiz_generator.get_system_prompt()},
        {"role": "user", "content": quiz_generator.build_user_prompt(
            content=content,
            num_questions=num_questions,
            question_type=question_type,
            difficulty=difficulty,
            topic=topic,
        )},
    ]

    # Call LLM
    response = await llm.generate(
        messages=messages,
        temperature=settings.default_temperature,
    )

    # Track usage
    usage_meta = track_usage(response, task="generate_quiz")

    # Validate output
    quiz, validation = await full_validation_pipeline(
        llm=llm,
        raw_output=response.content,
        schema_class=GeneratedQuiz,
        task_type="quiz_generation",
        context=content,
        skip_llm_validation=skip_llm_validation,
    )

    metadata = {
        "usage": usage_meta,
        "validation": validation.model_dump(),
        "latency_ms": response.latency_ms,
    }

    if quiz:
        logger.info(
            "generate_quiz completed",
            questions_count=len(quiz.questions),
            is_valid=validation.is_valid,
        )
    else:
        logger.warning("generate_quiz failed validation")

    return quiz, metadata

async def generate_diagnostic(
    llm: BaseLLM,
    content: str,
    num_questions: int = 3,
    topic: str = "",
) -> tuple[GeneratedQuiz | None, dict]:
    logger.info("generate_diagnostic started", topic=topic)

    messages = [
        {"role": "system", "content": quiz_generator.get_system_prompt()},
        {"role": "user", "content": quiz_generator.build_diagnostic_prompt(
            content=content,
            num_questions=num_questions,
            topic=topic,
        )},
    ]

    response = await llm.generate(
        messages=messages,
        temperature=settings.diagnostic_temperature,
    )

    usage_meta = track_usage(response, task="generate_diagnostic")

    quiz, validation = await full_validation_pipeline(
        llm=llm,
        raw_output=response.content,
        schema_class=GeneratedQuiz,
        task_type="diagnostic",
        context=content,
        skip_llm_validation=True,  # ← Selalu skip untuk kecepatan
    )

    return quiz, {"usage": usage_meta, "validation": validation.model_dump()}
