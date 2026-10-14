import sys
import os
from fastapi import APIRouter

# Add the AI directory to Python path so we can import nlp_module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "AI"))

from nlp_module import NLPModule

router = APIRouter()

# Initialize the NLP module (uses Ollama llama3.2:3b)
nlp = NLPModule()

@router.post("/query")
async def assistant_query(payload: dict):
    message = payload.get("message", "")
    session_id = payload.get("session_id", "")

    # Process through the real AI/NLP module
    result = nlp.process(message)

    return {
        "reply": result.get("reply", "Sorry, I couldn't process that."),
        "intent": result.get("intent"),
        "destination_id": result.get("destination"),
        "confidence": 1.0,
        "session_id": session_id,
        "error": result.get("_error")
    }