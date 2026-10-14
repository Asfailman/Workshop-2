"""
Module 1 - NLP Module
=====================
Conversational AI Guidance Assistant powered by Ollama (llama3.2:3b).

Responsibilities:
- Intent recognition (7 predefined intents)
- Entity extraction (destination, category, building)
- Multi-turn conversation context management
- Structured JSON output for downstream modules
"""

import json
import re
from typing import Optional

import ollama

# ---------------------------------------------------------------------------
# System prompt (mirrors NLP_Desc.md § 7)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an AI conversational guidance assistant for an educational environment.

ROLE:
Your role is to understand users' natural-language requests and help them find
information, request guidance, and identify suitable destinations within the
educational environment.

TASK:
For every user message, you must:
1. Identify the user's intent.
2. Extract relevant entities from the message.
3. Use previous conversation context when necessary.
4. Generate an appropriate response.

ALLOWED INTENTS:
The system must classify each user message into one of the following intents:

1. GREETING
2. LOCATION_QUERY
3. GUIDANCE_REQUEST
4. FACILITY_INFO
5. OPENING_HOURS
6. GENERAL_HELP
7. DESTINATION_RECOMMENDATION

Do not create new intent categories unless they are explicitly added to
the system design.

ENTITY RULES:
The system should extract the following entities when they are present:

1. destination:
   A specific place mentioned by the user.

2. category:
   A general type or purpose of destination mentioned by the user.

3. building:
   A building or area mentioned by the user.

If an entity is not mentioned or cannot be identified, return null.
Do not guess or invent entity values.

CONTEXT RULES:
1. Use previous conversation context when the user refers to a previously
   mentioned destination or category.

2. If the user uses references such as "it", "there", "that place", or
   similar expressions, resolve them using the most recent relevant context.

3. An explicitly mentioned destination or category in the current message
   takes priority over previous context.

4. If the user refers to a destination but there is no relevant previous
   context, ask the user for clarification instead of guessing.

5. When the user changes to a new destination or topic, update the relevant
   conversation context.

6. Do not assume information that has not been provided by the user or
   available system knowledge.

RESPONSE RULES:
1. Respond clearly and naturally to the user's request.
2. Keep the response relevant to the user's current intent.
3. If the user's request is unclear, ask a short clarification question.
4. Do not invent locations, facilities, opening hours, or other information.
5. If required information is unavailable, clearly state that the information
   is not available.
6. For DESTINATION_RECOMMENDATION, identify the user's category or request
   and pass the relevant information to Module 2.
7. For GUIDANCE_REQUEST, identify the destination and provide the information
   required for the guidance/navigation process.
8. Use previous conversation context when it is relevant to the current request.
9. Keep responses simple and suitable for students, staff, lecturers,
   and visitors.

OUTPUT FORMAT:
Always return the result in valid JSON format with the following fields:

{
  "intent": "string",
  "entities": {
    "destination": "string or null",
    "category": "string or null",
    "building": "string or null"
  },
  "reply": "string",
  "destination": "string or null"
}

OUTPUT RULES:
1. "intent" must contain exactly one of the allowed intents.
2. "entities" must contain: destination, category, building.
3. If an entity is not available, return null.
4. "reply" must contain the natural-language response to the user.
5. "destination" should contain the identified destination when applicable.
   Otherwise, return null.
6. Return valid JSON only.
7. Do not add explanations, markdown, or additional fields outside the
   defined JSON structure."""

# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------
ALLOWED_INTENTS = {
    "GREETING",
    "LOCATION_QUERY",
    "GUIDANCE_REQUEST",
    "FACILITY_INFO",
    "OPENING_HOURS",
    "GENERAL_HELP",
    "DESTINATION_RECOMMENDATION",
}

REQUIRED_ENTITIES = {"destination", "category", "building"}


# ---------------------------------------------------------------------------
# NLPModule
# ---------------------------------------------------------------------------
class NLPModule:
    """
    Wraps the Ollama chat API with multi-turn history and structured output.

    Args:
        model:   Ollama model name (default: llama3.2:3b).
        host:    Ollama server host (default: http://localhost:11434).
        options: Ollama model options dict (temperature, etc.).
    """

    def __init__(
        self,
        model: str = "llama3.2:3b",
        host: str = "http://localhost:11434",
        options: Optional[dict] = None,
    ):
        self.model = model
        self.options = options or {"temperature": 0.2}

        # Initialise Ollama client
        self.client = ollama.Client(host=host)

        # Conversation history: list of {"role": ..., "content": ...}
        # Begins with the system prompt
        self._history: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Internal context state (last known destination / category / building)
        self._context: dict = {
            "destination": None,
            "category": None,
            "building": None,
        }

        # Verify Ollama connection + model availability
        self._verify_model()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, user_message: str) -> dict:
        """
        Process a user message and return the structured result.

        Returns a dict containing:
            - intent, entities, reply, destination  (NLP output schema)
            - _context  (internal context state, for debugging)
            - _handoff  (navigation payload when applicable)
            - _error    (error description when parsing fails)
        """
        # Append user turn to history
        self._history.append({"role": "user", "content": user_message})

        # Call Ollama
        raw_response = self._call_ollama()

        # Append assistant turn to history
        self._history.append({"role": "assistant", "content": raw_response})

        # Parse and validate JSON
        result = self._parse_response(raw_response)

        # Update internal context
        self._update_context(result.get("entities", {}))

        # Attach internal debug fields
        result["_context"] = dict(self._context)

        # Build handoff payload for navigation intents
        if result.get("intent") in {"GUIDANCE_REQUEST", "DESTINATION_RECOMMENDATION"}:
            result["_handoff"] = self._build_handoff(result)

        return result

    def reset(self):
        """Clear conversation history and context (start a new session)."""
        self._history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._context = {"destination": None, "category": None, "building": None}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _verify_model(self):
        """Check that Ollama is reachable and the model is available."""
        try:
            available = [m.model for m in self.client.list().models]
        except Exception as exc:
            raise ValueError(
                f"Cannot connect to Ollama at the configured host. "
                f"Make sure Ollama is running. Error: {exc}"
            ) from exc

        # Accept model names with or without the ':latest' tag
        base = self.model.split(":")[0]
        match = any(m.split(":")[0] == base for m in available)
        if not match:
            raise ValueError(
                f"Model '{self.model}' is not available in Ollama. "
                f"Run: ollama pull {self.model}\n"
                f"Available models: {available}"
            )

    def _call_ollama(self) -> str:
        """Send the current history to Ollama and return the assistant content."""
        response = self.client.chat(
            model=self.model,
            messages=self._history,
            format="json",
            options=self.options,
        )
        return response.message.content.strip()

    def _parse_response(self, raw: str) -> dict:
        """
        Parse the LLM response into a validated dict.

        If the response is wrapped in markdown fences (``` ... ```) they are
        stripped before parsing.  If parsing or validation fails, a safe
        fallback dict is returned with an _error field.
        """
        # Strip DeepSeek-R1 <think>...</think> reasoning blocks
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", cleaned).strip().rstrip("`").strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Attempt to extract the first JSON object from mixed output
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    return self._error_result(
                        "Could not parse JSON from the model response.",
                        raw_reply=raw,
                    )
            else:
                return self._error_result(
                    "Model returned non-JSON output.",
                    raw_reply=raw,
                )

        return self._validate(data)

    def _validate(self, data: dict) -> dict:
        """Validate and normalise the parsed JSON against the output schema."""
        errors = []

        # --- intent ---
        intent = data.get("intent", "")
        if intent not in ALLOWED_INTENTS:
            errors.append(f"Invalid intent: '{intent}'")
            intent = "GENERAL_HELP"

        # --- entities ---
        raw_entities = data.get("entities", {})
        if not isinstance(raw_entities, dict):
            raw_entities = {}
            errors.append("'entities' field is not an object.")

        entities = {
            key: (raw_entities.get(key) if raw_entities.get(key) not in ("", "null") else None)
            for key in REQUIRED_ENTITIES
        }

        # --- reply ---
        reply = data.get("reply", "")
        if not reply:
            reply = "I'm sorry, I couldn't generate a response. Please try again."
            errors.append("'reply' field is empty.")

        # --- destination ---
        destination = data.get("destination")
        if destination in ("", "null"):
            destination = None

        result = {
            "intent": intent,
            "entities": entities,
            "reply": reply,
            "destination": destination,
        }

        if errors:
            result["_error"] = "; ".join(errors)

        return result

    def _update_context(self, entities: dict):
        """Update the session context with non-null entities from the latest turn."""
        for key in REQUIRED_ENTITIES:
            value = entities.get(key)
            if value is not None:
                self._context[key] = value

    def _build_handoff(self, result: dict) -> dict:
        """
        Build the handoff payload sent to Module 2 / Navigation subsystem.
        """
        return {
            "module": "Module2" if result["intent"] == "DESTINATION_RECOMMENDATION" else "Navigation",
            "intent": result["intent"],
            "destination": result.get("destination"),
            "category": result["entities"].get("category"),
            "building": result["entities"].get("building"),
        }

    @staticmethod
    def _error_result(error_msg: str, raw_reply: str = "") -> dict:
        """Return a safe fallback result when parsing fails."""
        return {
            "intent": "GENERAL_HELP",
            "entities": {"destination": None, "category": None, "building": None},
            "reply": "I'm sorry, I had trouble understanding that. Could you please rephrase?",
            "destination": None,
            "_error": error_msg,
            "_raw": raw_reply,
        }
