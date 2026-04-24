from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    model_name: str = Field(
        default="google/gemma-4-31b-it", alias="PATH_AI_MODEL"
    )
    timeout: int = Field(default=120, alias="PATH_AI_TIMEOUT")
    max_retries: int = Field(default=3, alias="PATH_AI_MAX_RETRIES")
    escalation_max_failures: int = Field(
        default=3, alias="PATH_AI_ESCALATION_MAX_FAILURES",
        description="Same topic asked N times = escalate to teacher"
    )
    default_temperature: float = 0.7
    grading_temperature: float = 0.2
    diagnostic_temperature: float = 0.3

    # Remedial
    remedial_threshold: float = Field(
        default=75.0, alias="PATH_AI_REMEDIAL_THRESHOLD",
        description="Score below this → status REMEDIAL"
    )

    # Tesseract OCR
    tesseract_cmd: Optional[str] = Field(default=None, alias="TESSERACT_CMD")

    # Upload
    upload_dir: str = Field(default="uploads", alias="PATH_AI_UPLOAD_DIR"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    # Cost tracking
    input_cost_per_million: float = Field(
        default=1.50, alias="PATH_AI_INPUT_COST_PER_M"
    )
    output_cost_per_million: float = Field(
        default=8.50, alias="PATH_AI_OUTPUT_COST_PER_M"
    )

# Singleton — import
settings = Settings()