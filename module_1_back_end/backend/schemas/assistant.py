from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class EntitiesSchema(BaseModel):
    destination: Optional[str] = Field(None, description="Specific destination identified")
    category: Optional[str] = Field(None, description="Category of destination")
    building: Optional[str] = Field(None, description="Building or block identified")


class AssistantQueryRequest(BaseModel):
    message: str = Field(..., description="Natural language query from user")
    session_id: str = Field(default="default", description="Conversation session ID for multi-turn context")
    current_location_id: Optional[str] = Field(default="", description="Current location ID of the robot/user")


class AssistantQueryResponse(BaseModel):
    reply: str = Field(..., description="Natural language response to show to user")
    intent: str = Field(..., description="Classified intent (e.g. GREETING, GUIDANCE_REQUEST, etc.)")
    destination_id: Optional[str] = Field(None, description="Identified destination name or ID")
    confidence: float = Field(default=1.0, description="Confidence score")
    entities: Optional[EntitiesSchema] = Field(None, description="Extracted entities")
    handoff: Optional[Dict[str, Any]] = Field(None, description="Downstream handoff payload for navigation/recommendation")
    route_info: Optional[Dict[str, Any]] = Field(None, description="Calculated navigation route when intent is GUIDANCE_REQUEST")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="Ranked destination recommendations when applicable")
    session_id: str = Field(..., description="Active session ID")
    error: Optional[str] = Field(None, description="Error message if any parsing or fallback occurred")
    transcribed_text: Optional[str] = Field(None, description="Transcribed user speech if input was provided as voice/audio")
    stt_duration_ms: Optional[float] = Field(None, description="Audio transcription duration in milliseconds")
    stt_engine: Optional[str] = Field(None, description="Speech-to-text engine used (e.g. whisper, google)")


class STTResponse(BaseModel):
    text: str = Field(..., description="Transcribed text from speech")
    engine: str = Field(..., description="Engine used (e.g. whisper, google)")
    duration_ms: float = Field(..., description="Transcription duration in milliseconds")
    language: Optional[str] = Field(None, description="Detected or specified audio language")


class AssistantResetRequest(BaseModel):
    session_id: str = Field(default="default", description="Session ID to clear dialogue context")
