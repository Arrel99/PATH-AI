from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.path_ai.core.openrouter_client import OpenRouterClient
from app.path_ai.tasks.tutor_chat import tutor_chat

router = APIRouter(prefix="/path-ai", tags=["PATH AI"])


class ChatRequest(BaseModel):
    student_message: str = Field(..., min_length=1)
    conversation_history: list[dict] = []
    context_material: str = ""
    subject: str = ""
    topic: str = ""


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
    finally:
        await llm.close()
