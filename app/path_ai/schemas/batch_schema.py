from pydantic import BaseModel, Field
from app.path_ai.schemas.quiz_schema import GeneratedQuiz


class BatchResult(BaseModel):
    source: str = Field(default="", description="Original filename")
    extracted_text_length: int = 0
    summary: str = Field(default="", description="AI-generated rangkuman materi")
    diagnostic_quiz: GeneratedQuiz | None = None
    post_test_quiz: GeneratedQuiz | None = None
    metadata: dict = Field(default_factory=dict)
