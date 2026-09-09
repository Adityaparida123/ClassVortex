from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.ai.assistant_service import process_message
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    message: str


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
