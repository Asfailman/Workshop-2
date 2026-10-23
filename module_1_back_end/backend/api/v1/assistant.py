import sys
import os
from fastapi import APIRouter

# Add the AI directory to Python path so we can import nlp_module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "AI"))

from nlp_module import NLPModule
from ...route_planner import get_route_for_destination

router = APIRouter()

# Initialize the NLP module (uses Ollama llama3.2:3b)
nlp = NLPModule()

# Intents that should trigger robot navigation
NAVIGATION_INTENTS = {"GUIDANCE_REQUEST", "DESTINATION_RECOMMENDATION"}

@router.post("/query")
async def assistant_query(payload: dict):
    message = payload.get("message", "")
    session_id = payload.get("session_id", "")

    # Process through the real AI/NLP module
    result = nlp.process(message)

    response = {
        "reply": result.get("reply", "Sorry, I couldn't process that."),
        "intent": result.get("intent"),
        "destination_id": result.get("destination"),
        "confidence": 1.0,
        "session_id": session_id,
        "error": result.get("_error"),
    }

    # If the AI detected a navigation intent, look up the route
    intent = result.get("intent", "")
    destination = result.get("destination")

    if intent in NAVIGATION_INTENTS and destination:
        route_info = get_route_for_destination(destination)
        response["navigation"] = {
            "available": route_info["found"],
            "destination_id": route_info["destination_id"],
            "route": route_info["route"],
            "route_summary": route_info["message"],
        }

        # Append route info to the AI reply so the user sees it in chat
        if route_info["found"]:
            response["reply"] += (
                f"\n\n🤖 Robot route ready! {route_info['message']}\n"
                f"The robot will now guide you to {route_info['destination_id']}."
            )

    return response