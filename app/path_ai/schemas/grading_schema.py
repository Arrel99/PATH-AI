from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class GradingStatus(str, Enum):
    PASSED = "passed"
    REMEDIAL = "remedial"


class MisconceptionDetail(BaseModel):
    concept: str = Field(default="", description="The concept student misunderstood")
    student_thinking: str = Field(
        default="", description="What the student likely thought"
    )
    correct_understanding: str = Field(
        default="", description="The correct concept explanation"
    )
    severity: str = Field(
        default="medium",
        description="low/medium/high — how critical is this misconception"
    )


class GradingFeedback(BaseModel):
    question_id: int = 0
    student_answer: str = ""
    correct_answer: str = ""
    is_correct: bool = False
    score: float = Field(default=0, ge=0, le=100, description="Score 0-100")
    explanation: str = Field(
        default="", description="Why this answer is correct/incorrect"
    )
    misconceptions: list[MisconceptionDetail] = Field(
        default_factory=list,
        description="Identified misconceptions (if incorrect)"
    )
    concept_feedback: str = Field(
        default="",
        description="Concept-based feedback for learning"
    )


class GradingResult(BaseModel):
    student_id: str
    quiz_id: str
    total_score: float = Field(..., ge=0, le=100)
    total_correct: int
    total_questions: int
    status: GradingStatus
    feedback: list[GradingFeedback] = Field(default_factory=list)
    weak_areas: list[str] = Field(
        default_factory=list,
        description="Topics/concepts that need remedial"
    )
    strong_areas: list[str] = Field(
        default_factory=list,
        description="Topics/concepts student understood well"
    )


class RemedialTrigger(BaseModel):
    needs_remedial: bool
    score: float
    threshold: float = 75.0
    weak_concepts: list[str] = Field(default_factory=list)
    misconceptions: list[MisconceptionDetail] = Field(default_factory=list)
    recommended_action: str = Field(
        default="",
        description="'ai_summary_card' | 'retake' | 'teacher_review'"
    )
