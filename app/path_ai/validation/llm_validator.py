from typing import Type
from pydantic import BaseModel
from app.path_ai.core.base_llm import BaseLLM
from app.path_ai.core.config import settings
from app.path_ai.prompts.validator import get_system_prompt, build_user_prompt
from app.path_ai.schemas.validation_schema import ValidationResult
from app.path_ai.validation.json_validator import validate_json
from app.path_ai.monitoring.logger import get_logger

logger = get_logger(__name__)


async def validate_with_llm(
    llm: BaseLLM,
    output_to_validate: str,
    expected_schema_name: str,
    task_type: str = "quiz_generation",
    context: str = "",
) -> ValidationResult:
    logger.info(
        "Starting LLM validation",
        task_type=task_type,
        output_length=len(output_to_validate),
    )

    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": build_user_prompt(
            original_output=output_to_validate,
            expected_schema=expected_schema_name,
            task_type=task_type,
            context=context,
        )},
    ]

    try:
        response = await llm.generate(
            messages=messages,
            temperature=settings.grading_temperature,  # Low temp for validation
        )

        # Parse the validation result
        result, parse_validation = validate_json(
            response.content,
            ValidationResult,
        )

        if result:
            result.validation_method = "llm"
            logger.info(
                "LLM validation complete",
                is_valid=result.is_valid,
                issue_count=len(result.issues),
            )
            return result

        # If we can't parse the LLM validator's own output, return cautious result
        logger.warning("Could not parse LLM validator response")
        return ValidationResult(
            is_valid=True,  # Don't block on validator failure
            issues=[],
            confidence_score=0.5,
            validation_method="llm",
        )

    except Exception as e:
        logger.error("LLM validation failed", error=str(e))
        # Don't block the pipeline if validation fails
        return ValidationResult(
            is_valid=True,
            issues=[],
            confidence_score=0.3,
            validation_method="llm",
        )


async def full_validation_pipeline(
    llm: BaseLLM,
    raw_output: str,
    schema_class: Type[BaseModel],
    task_type: str = "quiz_generation",
    context: str = "",
    skip_llm_validation: bool = False,
) -> tuple[BaseModel | None, ValidationResult]:
    # JSON + Schema validation
    model, json_result = validate_json(raw_output, schema_class)

    if not json_result.is_valid or model is None:
        return model, json_result

    # LLM re-validation 
    if not skip_llm_validation:
        import json
        llm_result = await validate_with_llm(
            llm=llm,
            output_to_validate=json.dumps(model.model_dump(), ensure_ascii=False),
            expected_schema_name=schema_class.__name__,
            task_type=task_type,
            context=context,
        )

        # Merge results
        combined = ValidationResult(
            is_valid=json_result.is_valid and llm_result.is_valid,
            issues=json_result.issues + llm_result.issues,
            corrected_output=llm_result.corrected_output,
            confidence_score=llm_result.confidence_score,
            validation_method="combined",
        )

        return model, combined

    return model, json_result
