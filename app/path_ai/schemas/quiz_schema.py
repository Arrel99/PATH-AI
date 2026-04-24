from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

#  Diagnostic Signal System 
class DiagnosticSignal(str, Enum):
    GREEN = "green"   
    YELLOW = "yellow"  

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    ESSAY = "essay"
    SHORT_ANSWER = "short_answer"

#  Quiz Structure 
class QuizOption(BaseModel):
    label: str = Field(..., description="Option label: A, B, C, D")
    text: str = Field(..., description="Option text content")
    is_correct: bool = Field(default=False)

class QuizQuestion(BaseModel):
    question_id: int = Field(..., description="Unique question number")
    question: str = Field(..., description="The question text")
    question_type: QuestionType = Field(default=QuestionType.MULTIPLE_CHOICE)
    options: list[QuizOption] = Field(default_factory=list)
    correct_answer: str = Field(..., description="Correct answer (label or text)")
    explanation: str = Field(default="", description="Why this is the correct answer")
    difficulty: str = Field(default="medium", description="easy/medium/hard")
    concept_tag: str = Field(default="", description="Related concept/topic")

class GeneratedQuiz(BaseModel):
    title: str = Field(..., description="Quiz title")
    subject: str = Field(default="")
    topic: str = Field(default="")
    total_questions: int = Field(..., description="Number of questions")
    questions: list[QuizQuestion] = Field(..., description="List of questions")
    summary: str = Field(default="", description="Content summary used to generate quiz")

#  Micro-Diagnostic 
class DiagnosticAnswer(BaseModel):
    question_id: int
    student_answer: str
    is_correct: bool
    concept_tag: str = ""

class DiagnosticResult(BaseModel):
    student_id: str
    signal: DiagnosticSignal
    answers: list[DiagnosticAnswer] = Field(default_factory=list)
    correct_count: int = 0
    total_count: int = 0
    weak_concepts: list[str] = Field(
        default_factory=list,
        description="Concepts where student needs more support"
    )
    recommended_path: str = Field(
        default="support",
        description="'fast-track' or 'support'"
    )