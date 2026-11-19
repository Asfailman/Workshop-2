from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from backend.schemas.assistant import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    AssistantResetRequest,
    STTResponse,
)
from backend.services.assistant_service import assistant_service
from backend.services.stt_service import stt_service

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
    "/chat/voice",
    response_model=AssistantQueryResponse,
    summary="Process speech audio input for assistant guidance",
    description="Transcribes user audio recording via Whisper/STT engine and processes the resulting text for campus navigation."
)
async def assistant_voice_query(
    file: UploadFile = File(..., description="Audio recording file (WAV, MP3, M4A, etc.)"),
    session_id: str = Form(default="default", description="Conversation session ID"),
    current_location_id: str = Form(default="", description="Optional starting/current location ID of user or robot"),
    language: Optional[str] = Form(default="en", description="Spoken language hint (e.g. en, ms)")
):
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file provided")

    # Debug: Save last received audio file for analysis
    try:
        os.makedirs("scratch", exist_ok=True)
        with open("scratch/last_debug_audio.wav", "wb") as dbg_f:
            dbg_f.write(audio_bytes)
        print(f"[assistant_voice_query] Received {len(audio_bytes)} bytes audio from client.")
    except Exception as e:
        print(f"[assistant_voice_query] Failed to save debug audio: {e}")

    # 1. Transcribe voice input using STT service
    stt_res = stt_service.transcribe(
        audio_bytes=audio_bytes,
        filename=file.filename or "recording.wav",
        language=language
    )

    transcribed_text = stt_res.get("text", "").strip()
    if not transcribed_text:
        return AssistantQueryResponse(
            reply="I couldn't hear or understand the audio clearly. Please try speaking again closer to the microphone!",
            intent="GENERAL_HELP",
            destination_id=None,
            confidence=0.0,
            entities=None,
            handoff=None,
            route_info=None,
            recommendations=None,
            session_id=session_id,
            error=stt_res.get("error") or "Transcription resulted in empty text",
            transcribed_text="",
            stt_duration_ms=stt_res.get("duration_ms"),
            stt_engine=stt_res.get("engine")
        )

    # 2. Process query through AssistantService
    query_result = await assistant_service.handle_query(
        session_id=session_id,
        message=transcribed_text,
        current_location_id=current_location_id or "",
    )

    # 3. Enrich response with STT transcription metadata
    query_result["transcribed_text"] = transcribed_text
    query_result["stt_duration_ms"] = stt_res.get("duration_ms")
    query_result["stt_engine"] = stt_res.get("engine")

    return query_result


@router.post(
    "/stt",
    response_model=STTResponse,
    summary="Transcribe speech audio to text",
    description="Standalone Speech-To-Text endpoint converting audio recording to text without triggering guidance logic."
)
async def transcribe_speech(
    file: UploadFile = File(..., description="Audio recording file"),
    language: Optional[str] = Form(default="en", description="Language hint (en, ms)")
):
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file provided")

    stt_res = stt_service.transcribe(
        audio_bytes=audio_bytes,
        filename=file.filename or "audio.wav",
        language=language
    )
    if not stt_res.get("success"):
        raise HTTPException(
            status_code=400,
            detail=stt_res.get("error", "Speech transcription failed")
        )

    return STTResponse(
        text=stt_res["text"],
        engine=stt_res["engine"],
        duration_ms=stt_res["duration_ms"],
        language=stt_res.get("language")
    )


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