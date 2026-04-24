from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from app.path_ai.core.openrouter_client import (
    OpenRouterClient, OpenRouterError, RateLimitError, ServiceUnavailableError,
)
from app.path_ai.tasks.tutor_chat import tutor_chat
from app.path_ai.tasks.generate_quiz import generate_quiz, generate_diagnostic
from app.path_ai.tasks.grade_answer import grade_single_answer, grade_quiz_attempt
from app.path_ai.tasks.simplify_content import simplify_content
from app.path_ai.tasks.generate_remedial import generate_remedial
from app.path_ai.tasks.generate_batch import generate_all_content
from app.path_ai.schemas.grading_schema import RemedialTrigger, MisconceptionDetail
from app.path_ai.core.config import settings
from app.path_ai.extractor.document_parser import parse_file
from app.path_ai.monitoring.logger import get_logger
from app.path_ai.engines.adaptive_engine import AdaptiveEngine
from app.path_ai.schemas.quiz_schema import DiagnosticAnswer
from app.path_ai.monitoring.token_tracker import get_tracker
from app.path_ai.monitoring.cost_tracker import get_cost_tracker
import os

logger = get_logger(__name__)

router = APIRouter(prefix="/path-ai", tags=["PATH AI"])

class ChatRequest(BaseModel):
    student_message: str = Field(..., min_length=1)
    conversation_history: list[dict] = []
    context_material: str = ""
    subject: str = ""
    topic: str = ""

class QuizRequest(BaseModel):
    content: str = Field(..., min_length=10)
    num_questions: int = Field(default=5, ge=1, le=20)
    question_type: str = "multiple_choice"
    difficulty: str = "medium"
    topic: str = ""
    skip_validation: bool = False

class DiagnosticRequest(BaseModel):
    content: str = Field(..., min_length=10, description="Materi untuk diagnostic")
    num_questions: int = Field(default=3, ge=1, le=10, description="Jumlah soal (default 3)")
    topic: str = Field(default="", description="Topik materi")


async def _save_upload(file: UploadFile) -> str:
    os.makedirs(settings.upload_dir, exist_ok=True)
    # Sanitize filename to prevent path traversal (e.g. "../../etc/passwd")
    safe_name = os.path.basename(file.filename) if file.filename else "upload"
    path = os.path.join(settings.upload_dir, safe_name)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return path

class GradeRequest(BaseModel):
    question: str = Field(..., min_length=1)
    correct_answer: str = Field(..., min_length=1)
    student_answer: str = Field(..., min_length=1)
    concept_tag: str = ""
    question_type: str = "multiple_choice"
class BatchGradeRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    quiz_id: str = Field(..., min_length=1)
    questions_and_answers: list[dict] = Field(
        ..., min_length=1,
        description="List of {question, correct_answer, student_answer, concept_tag}"
    )

class SimplifyRequest(BaseModel):
    content: str = Field(..., min_length=10, description="Materi yang akan disederhanakan")
    mode: str = Field(
        default="simplifier",
        description="'simplifier' (jalur kuning) atau 'fast-track' (jalur hijau)"
    )
    target_level: str = Field(default="SMA", description="Jenjang target: SD/SMP/SMA")
    topic: str = ""
    weak_concepts: list[str] = Field(
        default_factory=list,
        description="Konsep lemah dari diagnostic (hanya untuk mode simplifier)"
    )
class ClassifyRequest(BaseModel):
    student_id: str = ""
    answers: list[dict] = Field(
        ..., min_length=1,
        description="List of {question_id, student_answer, is_correct, concept_tag}"
    )

def _handle_openrouter_error(e: OpenRouterError):
    """Convert OpenRouter exceptions into proper HTTP responses."""
    if isinstance(e, RateLimitError):
        logger.warning("Rate limited by OpenRouter after all retries")
        raise HTTPException(
            status_code=429,
            detail="Model sedang sibuk (rate limited). Coba lagi dalam beberapa detik.",
        )
    if isinstance(e, ServiceUnavailableError):
        logger.warning(f"OpenRouter service unavailable: {e}")
        raise HTTPException(
            status_code=503,
            detail="Model sedang tidak tersedia. Coba lagi nanti.",
        )
    logger.error(f"OpenRouter error {e.status_code}: {e}")
    raise HTTPException(
        status_code=502,
        detail=f"Gagal menghubungi AI model (status {e.status_code}). Coba lagi nanti.",
    )

class RemedialRequest(BaseModel):
    score: float = Field(..., ge=0, le=100)
    threshold: float = Field(default=75.0)
    weak_concepts: list[str] = Field(default_factory=list)
    misconceptions: list[dict] = Field(default_factory=list)
    original_content: str = ""
    student_level: str = "SMA"

@router.post("/tanya-tutor")
async def api_tutor_chat(req: ChatRequest):
    llm = OpenRouterClient()
    try:
        result = await tutor_chat(
            llm=llm,
            student_message=req.student_message,
            conversation_history=req.conversation_history or None,
            context_material=req.context_material,
            subject=req.subject,
            topic=req.topic,
        )
        return result
    except OpenRouterError as e:
        _handle_openrouter_error(e)
    finally:
        await llm.close()

@router.post("/buat-soal-quiz")
async def api_generate_quiz(req: QuizRequest):
    llm = OpenRouterClient()
    try:
        quiz, meta = await generate_quiz(
            llm=llm, content=req.content, num_questions=req.num_questions,
            question_type=req.question_type, difficulty=req.difficulty,
            topic=req.topic, skip_llm_validation=req.skip_validation,
        )
        if not quiz:
            raise HTTPException(status_code=500, detail="Quiz generation failed")
        return {"quiz": quiz.model_dump(), "metadata": meta}
    except OpenRouterError as e:
        _handle_openrouter_error(e)
    finally:
        await llm.close()

@router.post("/upload-dan-extract")
async def api_parse_upload(file: UploadFile = File(...)):
    path = await _save_upload(file)
    try:
        result = parse_file(path)
        return {
            "text": result["text"],
            "text_length": len(result["text"]),
            "image_count": len(result["images"]),
            "page_count": result["page_count"],
            "source": result["source"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(path):
            os.remove(path)

@router.post("/buat-soal-diagnostic")
async def api_generate_diagnostic(req: DiagnosticRequest):
    llm = OpenRouterClient()
    try:
        quiz, meta = await generate_diagnostic(
            llm=llm,
            content=req.content,
            num_questions=req.num_questions,
            topic=req.topic,
        )
        if not quiz:
            raise HTTPException(status_code=500, detail="Diagnostic generation failed")
        return {"quiz": quiz.model_dump(), "metadata": meta}
    except OpenRouterError as e:
        _handle_openrouter_error(e)
    finally:
        await llm.close()

@router.post("/nilai-satu-jawaban")
async def api_grade_single(req: GradeRequest):
    llm = OpenRouterClient()
    try:
        feedback, meta = await grade_single_answer(
            llm=llm,
            question=req.question,
            correct_answer=req.correct_answer,
            student_answer=req.student_answer,
            concept_tag=req.concept_tag,
            question_type=req.question_type,
        )
        if not feedback:
            raise HTTPException(status_code=500, detail="Grading failed")
        return {"feedback": feedback.model_dump(), "metadata": meta}
    except OpenRouterError as e:
        _handle_openrouter_error(e)
    finally:
        await llm.close()

@router.post("/nilai-semua-jawaban")
async def api_grade_batch(req: BatchGradeRequest):
    llm = OpenRouterClient()
    try:
        result, remedial, meta = await grade_quiz_attempt(
            llm=llm,
            student_id=req.student_id,
            quiz_id=req.quiz_id,
            questions_and_answers=req.questions_and_answers,
        )
        if not result:
            raise HTTPException(status_code=500, detail="Batch grading failed")
        return {
            "result": result.model_dump(),
            "remedial": remedial.model_dump(),
            "metadata": meta,
        }
    except OpenRouterError as e:
        _handle_openrouter_error(e)
    finally:
        await llm.close()

@router.post("/sederhanakan-materi")
async def api_simplify_content(req: SimplifyRequest):
    llm = OpenRouterClient()
    try:
        simplified, meta = await simplify_content(
            llm=llm,
            content=req.content,
            mode=req.mode,
            target_level=req.target_level,
            topic=req.topic,
            weak_concepts=req.weak_concepts or None,
        )
        return {"simplified_content": simplified, "metadata": meta}
    except OpenRouterError as e:
        _handle_openrouter_error(e)
    finally:
        await llm.close()
@router.post("/klasifikasi-sinyal")
async def api_classify_diagnostic(req: ClassifyRequest):
    engine = AdaptiveEngine()
    answers = [DiagnosticAnswer(**a) for a in req.answers]
    result = engine.classify_diagnostic(answers=answers, student_id=req.student_id)
    return result.model_dump()

@router.post("/buat-remedial")
async def api_generate_remedial(req: RemedialRequest):
    trigger = RemedialTrigger(
        needs_remedial=req.score < req.threshold,
        score=req.score, threshold=req.threshold,
        weak_concepts=req.weak_concepts,
    )
    trigger.misconceptions = [MisconceptionDetail(**m) for m in req.misconceptions]
    if not trigger.needs_remedial:
        return {"remedial_content": "", "skipped": True}
    llm = OpenRouterClient()
    try:
        content, meta = await generate_remedial(
            llm=llm, remedial_trigger=trigger,
            original_content=req.original_content,
            student_level=req.student_level,
        )
        return {"remedial_content": content, "metadata": meta}
    except OpenRouterError as e:
        _handle_openrouter_error(e)
    finally:
        await llm.close()

@router.get("/lihat-pemakaian")
async def api_usage():
    tracker = get_tracker()
    cost = get_cost_tracker()
    return {
        "tokens": tracker.get_total(),
        "cost": cost.get_summary(),
    }

@router.post("/generate-semua-konten")
async def api_generate_all(
    file: UploadFile = File(...),
    topic: str = "",
    subject: str = "",
    num_diagnostic: int = 5,
    num_post_test: int = 10,
):
    path = await _save_upload(file)
    llm = OpenRouterClient()
    try:
        result = await generate_all_content(
            llm=llm, file_path=path, topic=topic, subject=subject,
            num_diagnostic=num_diagnostic, num_post_test=num_post_test,
        )
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OpenRouterError as e:
        _handle_openrouter_error(e)
    finally:
        await llm.close()
        if os.path.exists(path):
            os.remove(path)