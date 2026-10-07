import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure the AI module directory is in sys.path
# Checks both parent directory (repo root/AI) and current project layout
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parents[2]
AI_DIR = REPO_ROOT / "AI"

if AI_DIR.exists() and str(AI_DIR) not in sys.path:
    sys.path.insert(0, str(AI_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from nlp_module import NLPModule
except ImportError:
    try:
        from AI.nlp_module import NLPModule
    except ImportError:
        NLPModule = None


class AssistantService:
    """
    Assistant service integrating Member 2's NLPModule (Ollama LLM)
    with session management and multi-turn context support.
    """

    def __init__(self, default_model: str = "llama3.2:3b"):
        self.default_model = default_model
        self._sessions: Dict[str, Any] = {}

    def get_or_create_session(self, session_id: str):
        """Retrieve existing NLPModule instance for the session or create a new one."""
        if session_id not in self._sessions:
            if NLPModule is None:
                raise RuntimeError("NLPModule could not be imported from AI/nlp_module.py")
            self._sessions[session_id] = NLPModule(model=self.default_model)
        return self._sessions[session_id]

    def reset_session(self, session_id: str) -> bool:
        """Clear conversation history and context for a specific session."""
        if session_id in self._sessions:
            self._sessions[session_id].reset()
            return True
        return False

    async def handle_query(
        self, session_id: str, message: str, current_location_id: str = ""
    ) -> Dict[str, Any]:
        """
        Processes user natural language input via NLPModule.
        Returns a dictionary conforming to the Module 1 API contract:
        {
            "reply": str,
            "intent": str,
            "destination_id": Optional[str],
            "confidence": float,
            "entities": dict,
            "handoff": Optional[dict],
            "session_id": str,
            "error": Optional[str]
        }
        """
        session_id = session_id or "default"

        try:
            nlp = self.get_or_create_session(session_id)
            result = nlp.process(message)

            return {
                "reply": result.get("reply", "I'm here to help."),
                "intent": result.get("intent", "GENERAL_HELP"),
                "destination_id": result.get("destination"),
                "confidence": 1.0 if not result.get("_error") else 0.5,
                "entities": result.get("entities", {
                    "destination": None,
                    "category": None,
                    "building": None
                }),
                "handoff": result.get("_handoff"),
                "session_id": session_id,
                "error": result.get("_error"),
            }

        except Exception as exc:
            # Fallback if Ollama service is unavailable or encounters an error
            return {
                "reply": (
                    "I am currently having trouble connecting to my AI service. "
                    "Please verify that Ollama is running."
                ),
                "intent": "GENERAL_HELP",
                "destination_id": None,
                "confidence": 0.0,
                "entities": {
                    "destination": None,
                    "category": None,
                    "building": None
                },
                "handoff": None,
                "session_id": session_id,
                "error": str(exc),
            }


# Singleton instance for easy dependency injection
assistant_service = AssistantService()