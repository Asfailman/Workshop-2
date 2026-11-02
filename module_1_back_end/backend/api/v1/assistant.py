from fastapi import APIRouter, status
from backend.schemas.assistant import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    AssistantResetRequest,
)
from backend.services.assistant_service import assistant_service

router = APIRouter()


@router.post(
    "/query",
    response_model=AssistantQueryResponse,
    summary="Process user natural language query",
    description="Passes user utterance to the AI NLP module and returns guidance/intent output."
)
async def assistant_query(payload: AssistantQueryRequest):
    result = await assistant_service.handle_query(
        session_id=payload.session_id,
        message=payload.message,
        current_location_id=payload.current_location_id or "",
    )
    return result


@router.post(
    "/reset",
    summary="Reset assistant dialogue context",
    description="Resets multi-turn conversation context for a specified session ID."
)
async def reset_session(payload: AssistantResetRequest):
    success = assistant_service.reset_session(payload.session_id)
    return {
        "status": "ok",
        "session_id": payload.session_id,
        "reset": success,
        "message": f"Session '{payload.session_id}' context has been reset."
    }