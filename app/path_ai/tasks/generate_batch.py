from app.path_ai.core.base_llm import BaseLLM
from app.path_ai.extractor.document_parser import parse_file
from app.path_ai.tasks.generate_quiz import generate_quiz, generate_diagnostic
from app.path_ai.tasks.simplify_content import simplify_content
from app.path_ai.schemas.batch_schema import BatchResult
from app.path_ai.monitoring.logger import get_logger
from app.path_ai.monitoring.token_tracker import get_tracker

logger = get_logger(__name__)


async def generate_all_content(
    llm: BaseLLM,
    file_path: str,
    topic: str = "",
    subject: str = "",
    num_diagnostic: int = 5,
    num_post_test: int = 10,
) -> BatchResult:
    logger.info("Batch generation started", file=file_path, topic=topic)

    # Parse document
    parsed = parse_file(file_path)
    content = parsed["text"]
    if not content.strip():
        raise ValueError("Extracted text is empty. Check your file.")

    # Generate rangkuman
    summary, summary_meta = await simplify_content(
        llm=llm, content=content, mode="simplifier",
        target_level="SMA", topic=topic,
    )

    #  Generate diagnostic quiz
    diagnostic, diag_meta = await generate_diagnostic(
        llm=llm, content=content, num_questions=num_diagnostic, topic=topic,
    )

    # Generate post-test quiz
    post_test, post_meta = await generate_quiz(
        llm=llm, content=content, num_questions=num_post_test,
        question_type="multiple_choice", difficulty="medium",
        topic=topic, skip_llm_validation=True,
    )

    tracker = get_tracker()

    return BatchResult(
        source=parsed["source"],
        extracted_text_length=len(content),
        summary=summary,
        diagnostic_quiz=diagnostic,
        post_test_quiz=post_test,
        metadata={
            "topic": topic, "subject": subject,
            "summary_meta": summary_meta,
            "diagnostic_meta": diag_meta,
            "post_test_meta": post_meta,
            "total_tokens": tracker.get_total(),
            "image_count": len(parsed["images"]),
        },
    )