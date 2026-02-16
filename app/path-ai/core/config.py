from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    model_name: str = Field(
        default="qwen/qwen3-vl-235b-a22b-thinking", alias="PATH_AI_MODEL"
    )
    timeout: int = Field(default=120, alias="PATH_AI_TIMEOUT")
    max_retries: int = Field(default=3, alias="PATH_AI_MAX_RETRIES")
    escalation_max_failures: int = Field(
        default=3, alias="PATH_AI_ESCALATION_MAX_FAILURES",
        description="Same topic asked N times = escalate to teacher"
    )
    default_temperature: float = 0.7

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton — import 
settings = Settings()