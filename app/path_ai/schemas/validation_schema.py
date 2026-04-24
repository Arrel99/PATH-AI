from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    field: str = Field(..., description="Which field has the issue")
    issue: str = Field(..., description="Description of the issue")
    severity: str = Field(default="warning", description="warning/error/critical")
    suggestion: str = Field(default="", description="How to fix this")


class ValidationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether the output is valid")
    issues: list[ValidationIssue] = Field(default_factory=list)
    corrected_output: str | None = Field(
        default=None,
        description="Auto-corrected output if fixable"
    )
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="How confident are we in this output"
    )
    validation_method: str = Field(
        default="json",
        description="'json' | 'llm' | 'combined'"
    )
