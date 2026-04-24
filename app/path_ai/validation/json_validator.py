import json
import re
from typing import Any, Type, TypeVar
from pydantic import BaseModel, ValidationError
from app.path_ai.schemas.validation_schema import ValidationResult, ValidationIssue
from app.path_ai.monitoring.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


def extract_json_from_text(raw_text: str) -> str:
    # JSON in code blocks
    code_block_match = re.search(
        r"```(?:json)?\s*\n?([\s\S]*?)\n?```",
        raw_text,
        re.DOTALL,
    )
    if code_block_match:
        return code_block_match.group(1).strip()

    # JSON object or array
    json_patterns = [
        re.compile(r"(\{[\s\S]*\})", re.DOTALL),   # Object
        re.compile(r"(\[[\s\S]*\])", re.DOTALL),    # Array
    ]

    for pattern in json_patterns:
        match = pattern.search(raw_text)
        if match:
            return match.group(1).strip()

    # return as-is
    return raw_text.strip()


def fix_common_json_issues(json_str: str) -> str:
    # Remove trailing commas before } or ]
    fixed = re.sub(r",\s*([}\]])", r"\1", json_str)

    # Count brackets
    open_braces = fixed.count("{")
    close_braces = fixed.count("}")
    open_brackets = fixed.count("[")
    close_brackets = fixed.count("]")

    # Add missing closing brackets
    fixed += "}" * (open_braces - close_braces)
    fixed += "]" * (open_brackets - close_brackets)

    return fixed


def validate_json(
    raw_text: str,
    schema_class: Type[T],
    auto_fix: bool = True,
) -> tuple[T | None, ValidationResult]:
    issues: list[ValidationIssue] = []

    # Extract JSON
    json_str = extract_json_from_text(raw_text)

    # Try parsing
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        if auto_fix:
            logger.warning("JSON parse failed, attempting auto-fix", error=str(e))
            fixed = fix_common_json_issues(json_str)
            try:
                data = json.loads(fixed)
                issues.append(ValidationIssue(
                    field="json",
                    issue=f"JSON had errors, auto-fixed: {e}",
                    severity="warning",
                    suggestion="Improve prompt to generate cleaner JSON",
                ))
            except json.JSONDecodeError as e2:
                logger.error("JSON auto-fix failed", error=str(e2))
                return None, ValidationResult(
                    is_valid=False,
                    issues=[ValidationIssue(
                        field="json",
                        issue=f"Invalid JSON even after auto-fix: {e2}",
                        severity="critical",
                    )],
                    validation_method="json",
                )
        else:
            return None, ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    field="json",
                    issue=f"Invalid JSON: {e}",
                    severity="critical",
                )],
                validation_method="json",
            )

    # Validate against Pydantic schema
    try:
        model = schema_class.model_validate(data)
        logger.info(
            "JSON validation passed",
            schema=schema_class.__name__,
        )
        return model, ValidationResult(
            is_valid=True,
            issues=issues,
            validation_method="json",
        )
    except ValidationError as e:
        for error in e.errors():
            issues.append(ValidationIssue(
                field=".".join(str(loc) for loc in error["loc"]),
                issue=error["msg"],
                severity="error",
                suggestion=f"Expected type: {error.get('type', 'unknown')}",
            ))

        logger.warning(
            "Schema validation failed",
            schema=schema_class.__name__,
            error_count=len(e.errors()),
        )

        return None, ValidationResult(
            is_valid=False,
            issues=issues,
            validation_method="json",
        )
