from app.path_ai.core.base_llm import BaseLLM
from app.path_ai.core.config import settings
from app.path_ai.prompts import grader
from app.path_ai.schemas.grading_schema import (
    GradingResult,
    GradingFeedback,
    GradingStatus,
    RemedialTrigger,
)
from app.path_ai.validation.json_validator import validate_json
from app.path_ai.monitoring.logger import get_logger
from app.path_ai.monitoring.token_tracker import track_usage

logger = get_logger(__name__)


async def grade_single_answer(
    llm: BaseLLM,
    question: str,
    correct_answer: str,
    student_answer: str,
    concept_tag: str = "",
    question_type: str = "multiple_choice",
) -> tuple[GradingFeedback | None, dict]:
    messages = [
        {"role": "system", "content": grader.get_system_prompt()},
        {"role": "user", "content": grader.build_user_prompt(
            question=question,
            correct_answer=correct_answer,
            student_answer=student_answer,
            concept_tag=concept_tag,
            question_type=question_type,
        )},
    ]

    response = await llm.generate(
        messages=messages,
        temperature=settings.grading_temperature,
    )

    usage_meta = track_usage(response, task="grade_answer")

    feedback, validation = validate_json(response.content, GradingFeedback)

    # Fill caller-provided context that LLM doesn't return
    if feedback:
        feedback.student_answer = student_answer
        feedback.correct_answer = correct_answer

    return feedback, {"usage": usage_meta, "validation": validation.model_dump()}


async def grade_quiz_attempt(
    llm: BaseLLM,
    student_id: str,
    quiz_id: str,
    questions_and_answers: list[dict],
) -> tuple[GradingResult | None, RemedialTrigger, dict]:
    logger.info(
        "grade_quiz_attempt started",
        student_id=student_id,
        quiz_id=quiz_id,
        answer_count=len(questions_and_answers),
    )

    # Grade all answers via batch prompt
    messages = [
        {"role": "system", "content": grader.get_system_prompt()},
        {"role": "user", "content": grader.build_batch_grading_prompt(
            questions_and_answers=questions_and_answers,
        )},
    ]

    response = await llm.generate(
        messages=messages,
        temperature=settings.grading_temperature,
    )

    usage_meta = track_usage(response, task="grade_quiz")

    # Parse individual feedback items
    from app.path_ai.validation.json_validator import extract_json_from_text
    import json

    try:
        raw_json = extract_json_from_text(response.content)
        feedback_data = json.loads(raw_json)
        if isinstance(feedback_data, dict):
            feedback_data = feedback_data.get("feedback", [feedback_data])
    except (json.JSONDecodeError, KeyError):
        logger.error("Failed to parse batch grading response")
        return None, RemedialTrigger(
            needs_remedial=False, score=0, threshold=settings.remedial_threshold,
        ), {"usage": usage_meta}

    # Build feedback list
    feedbacks: list[GradingFeedback] = []
    for item in feedback_data:
        try:
            fb = GradingFeedback.model_validate(item)
            feedbacks.append(fb)
        except Exception as e:
            logger.warning("Failed to parse feedback item", error=str(e))

    # Calculate totals
    total_correct = sum(1 for f in feedbacks if f.is_correct)
    total_questions = len(feedbacks) or len(questions_and_answers)
    total_score = (total_correct / total_questions * 100) if total_questions > 0 else 0

    # Determine status
    status = (
        GradingStatus.PASSED
        if total_score >= settings.remedial_threshold
        else GradingStatus.REMEDIAL
    )

    # ⑥ Collect weak areas and misconceptions
    weak_areas = list(set(
        qa.get("concept_tag", "")
        for qa, fb in zip(questions_and_answers, feedbacks)
        if not fb.is_correct and qa.get("concept_tag")
    ))

    strong_areas = list(set(
        qa.get("concept_tag", "")
        for qa, fb in zip(questions_and_answers, feedbacks)
        if fb.is_correct and qa.get("concept_tag")
    ))

    all_misconceptions = []
    for fb in feedbacks:
        all_misconceptions.extend(fb.misconceptions)

    # ⑦ Build result
    grading_result = GradingResult(
        student_id=student_id,
        quiz_id=quiz_id,
        total_score=round(total_score, 2),
        total_correct=total_correct,
        total_questions=total_questions,
        status=status,
        feedback=feedbacks,
        weak_areas=weak_areas,
        strong_areas=strong_areas,
    )

    # ⑧ Build remedial trigger
    remedial_trigger = RemedialTrigger(
        needs_remedial=status == GradingStatus.REMEDIAL,
        score=round(total_score, 2),
        threshold=settings.remedial_threshold,
        weak_concepts=weak_areas,
        misconceptions=all_misconceptions,
        recommended_action=(
            "ai_summary_card" if status == GradingStatus.REMEDIAL else ""
        ),
    )

    logger.info(
        "grade_quiz_attempt completed",
        score=total_score,
        status=status.value,
        needs_remedial=remedial_trigger.needs_remedial,
    )

    return grading_result, remedial_trigger, {"usage": usage_meta}
