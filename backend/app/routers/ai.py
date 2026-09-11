from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.ai.assistant_service import process_message
from app.ai.llm_client import llm_client
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    message: str


@router.get("/status", response_model=dict)
@router.get("/health", response_model=dict)
async def ai_status():
    """Public, secret-free connectivity check for the AI service.

    Registered at both /api/v1/ai/status and /api/v1/ai/health (alias).
    Never crashes when the LLM provider is down: it returns a controlled
    {"available": false, "reason": ...} payload instead.
    """
    status = await llm_client.health()
    return {"success": True, "data": status}


@router.post("/chat", response_model=dict)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    result = await process_message(request.message, str(current_user["_id"]))
    ans = result.get("answer", "")
    return {
        "success": True,
        "data": {
            **result,
            "answer": ans,
            "message": ans,
        },
    }
