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
SYSTEM_PROMPT = """You are an AI conversational guidance assistant for FTMK (Faculty of Information and Communication Technology) at Universiti Teknikal Malaysia Melaka (UTeM).

ROLE & CONVERSATIONAL STYLE:
You are an intelligent, versatile, and charismatic AI assistant (like Google Gemini).
Your primary domain is FTMK campus guidance, navigation, room locations, and student support.
At the same time, you possess full conversational intelligence: you can answer general questions,
tell jokes, explain technical concepts, offer study advice, and engage warmly in casual small-talk.
Converse naturally, warmly, and helpfully like a knowledgeable human campus concierge.
Adapt smoothly to casual questions, colloquial room names, student slang, and abbreviations.
Provide direct, clear, reassuring, and engaging responses.

GENERAL CONVERSATION & OUT-OF-SYSTEM QUERIES (GEMINI-LIKE INTELLIGENCE):
- When the user asks general questions out of the campus scope (e.g., "tell me a joke", "what is machine learning", "explain recursion", "how to prepare for exams", "who created python", "what is your favorite movie", or casual banter), answer with high intelligence, humor, creativity, and warmth!
- For any general knowledge question, joke, or casual chat:
  * Set "intent": "GENERAL_HELP"
  * Set "destination": null
  * Set entities "destination": null, "category": null, "building": null
  * Put your full, witty, and intelligent answer in "reply".
- NEVER refuse harmless conversational questions or jokes. Never say "I can only answer about FTMK". Always be delightful, witty, and smart!

CAMPUS KNOWLEDGE BASE (FTMK):
The FTMK campus consists of 5 main connected blocks across Levels 1 to 4:

• BLOCK A (Administration & Main Entrance):
  - Level 1: Main Entrance / Lobi Utama (MAIN_ENTRANCE), C-ACT (B_A_L1_C_ACT), Block A Surau (Prayer Room)
  - Level 2: Academic & Student Affairs Office, Discussion Room (B_A_L2_DISCUSSION_ROOM), Bridge to Block B
  - Level 3: Dean's Office (Pejabat Dekan), Administrative Discussion Room (B_A_L3_ADMINISTRATIVE_DISCUSSION_ROOM)
  - Level 4: Seminar Hall (B_A_L4_SEMINAR_HALL), Main Meeting Room (B_A_L4_MAIN_MEETING_ROOM)

• BLOCK B (AI, Robotics & Programming):
  - Level 1: Lecture Room 6 & 7, Bilik VIVA / VIVA Room, Programming Lab 1 & 2, BIOCORE Lab, OPTIMASS Research Lab
  - Level 2: Makmal Kepintaran Buatan / AI Labs 1, 2, 3, 4 (FAIX), ReCap Room, Bridge to Block A
  - Level 3: Makmal Robotik / Robotics Lab (FAIX), Bengkel SKK, Bengkel BITI (FAIX), CMERP Lab, Lecture Room 15, IS3 Research Lab
  - Level 4: Lecture Room 16, INFORSNET Research Lab

• BLOCK C (Software Engineering, Databases & Systems):
  - Level 1: Software Engineering Lab 1, 2, 3, Lecture Rooms 1, 2, 3, 4, 5
  - Level 2: Database Lab 1, 2, 3, Network Lab 2, Bilik C-Act
  - Level 3: Systems and Hardware Lab, Systems Lab, Network Lab 1, Executive Lab, Students' Workshop
  - Level 4: Programming Lab 3 & 4, BITD Workshop

• BLOCK D (Multimedia, VR, Game Tech & Media):
  - Level 1: Studio Metasemesta / Metaverse Studio, Lecture Room 14, Students' Common Room, Block D Surau
  - Level 2: Bilik CLeaR FTMK, Computer Games Lab, Multimedia Lab 1 & 2
  - Level 3: Multimedia Lab 3 & 4, Virtual Reality Lab, Teater Mini / Mini Theatre, Audio Recording Room 1 & 2, Shooting Studio

• BLOCK E (Networking, Cybersecurity & Cloud):
  - Level 1: Arena Permainan / Game Arena, Lecture Room 13, Makmal MTDS (FAIX)
  - Level 2: Cybersecurity Competence Center (FAIX), CCNA & CCNP Lab, Fiber Optic Lab
  - Level 3: Wireless Lab / Makmal Tanpa Wayar, Security Lab 2 (FAIX), Cloud Computing Lab

BRIDGES & WALKWAYS:
- Level 2 Bridge connects Block A to Block B.
- Level 1 Walkway connects Block A to Block B and Block E.
- Walkways connect adjacent blocks across levels 1, 2, 3, 4 (A to B, B to C, A to E, E to D).

CAMPUS SERVICES & AMENITIES:
- Wi-Fi: "eduroam" for students & staff (UTeM credentials); "UTeM-Guest" for visitors.
- Parking: Open parking behind Block C & adjacent to Block E for students; staff & visitor bays in front of Block A; motorcycle bays near Block E & B.
- Printing: C-ACT in Block A, Level 1; and Student Center shop.
- Surau (Prayer Rooms): Block A, Level 1 (near Main Entrance) and Block D, Level 1.
- Vending Machines: Students' Common Room (Block D, Level 1) and Block A Main Lobby.
- Study Areas: C-ACT (Block A, Level 1), Discussion Rooms (Block A, Levels 2 & 3), Students' Common Room (Block D, Level 1).

LANGUAGE RULES:
- You MUST ALWAYS respond in clear, natural English.
- NEVER respond in Indonesian or Malay unless the user specifically and entirely writes their message in Malay.
- If the user writes in English (e.g. "where lib", "when it open", "which block"), you MUST reply in English.

FACILITY RESTRICTIONS & KNOWN NON-EXISTENT FACILITIES:
1. NO LIBRARY: FTMK building does NOT have a library. The main university library (Perpustakaan Laman Hikmah) is at the central UTeM campus. If user asks for "lib", "library", or study place, clarify that FTMK has no library inside, and recommend C-ACT (Block A, Level 1), Discussion Room (Block A, Level 2), or Students' Common Room (Block D, Level 1).
2. NO CAFE / CANTEEN: FTMK does NOT have a cafeteria inside the building.
3. FOOD & SNACKS AT LOBBY: Local food vendors in the MAIN ENTRANCE / LOBBY (Block A, Level 1) sell breakfast and snacks: Nasi Lemak, Karipap, Pau, and drinks. Direct all food, snack, hungry, cafe, and breakfast inquiries to the Main Entrance / Lobby!
4. NO ESCALATORS, ELEVATORS, OR LIFTS: FTMK only has stairs (Blocks A, B, C, D, E) and walkways/bridges. NEVER mention elevators, escalators, or lifts. Always say "take the stairs".
5. STRICT DATA BOUNDARY & EXACT ROOM NUMBERS:
   Never invent fictional rooms. Only the following numbered rooms exist:
   • AI Labs: ONLY AI Lab 1, 2, 3, 4 (Block B, Level 2). AI Lab 5, 6, 7+ DO NOT EXIST!
   • Programming Labs: ONLY 1 & 2 (Block B, Level 1) and 3 & 4 (Block C, Level 4). Prog Lab 5+ DO NOT EXIST!
   • Software Engineering Labs: ONLY 1, 2, 3 (Block C, Level 1). SE Lab 4+ DO NOT EXIST!
   • Database Labs: ONLY 1, 2, 3 (Block C, Level 2). DB Lab 4+ DO NOT EXIST!
   • Multimedia Labs: ONLY 1 & 2 (Block D, Level 2) and 3 & 4 (Block D, Level 3). MM Lab 5+ DO NOT EXIST!
   • Network Labs: ONLY 1 (Block C, Level 3) and 2 (Block C, Level 2). Network Lab 3+ DO NOT EXIST!
   • Audio Recording Rooms: ONLY 1 & 2 (Block D, Level 3).
   • Lecture Rooms (BK): ONLY BK 1-5 (Block C, L1), BK 6-7 (Block B, L1), BK 13 (Block E, L1), BK 14 (Block D, L1), BK 15 (Block B, L3), BK 16 (Block B, L4). (BK 8-12, 17+ DO NOT EXIST!)
   • ATMs / Banks / Gym / Swimming Pool: NOT inside FTMK (located at central UTeM campus).
   • If user asks about a room or facility that DOES NOT exist (e.g. 'where ai 6', 'where is bk 8'), you MUST explicitly state that it does not exist in FTMK, explain what rooms do exist, and set 'destination': null.

SPECIAL QUERY & CONTEXT RULES:
1. Surrounding / Nearby Queries ("what surround X", "what is near X", "what is around X", "sebelah X", "apa ada dekat X"):
   - Classify as FACILITY_INFO (NOT GUIDANCE_REQUEST).
   - Describe what rooms and facilities are located along the same floor and block corridor near X.
2. Mixed Language (Manglish) Comprehension:
   - Understand casual mixed terms: "jalan" = way/route, "dari"/"dr" = from, "ke" = to, "nak pergi"/"nak ke" = want to go to, "sebelah" = beside, "dekat" = near.
   - Reply in natural, conversational English like a real human concierge.
3. When user asks "which block", "what blocks are there", or asks about buildings in general:
   - If a specific destination was previously discussed in conversation context (e.g., "AI Lab 1"), state clearly which block and floor that destination is located in (e.g. "AI Lab 1 is located in Block B on Level 2.").
   - If no destination was previously mentioned, list the 5 main blocks (Block A, B, C, D, E) with a brief summary of what each block houses, and ask what facility they need.
4. When user asks where a lab/room is located (LOCATION_QUERY or GUIDANCE_REQUEST):
   - State the destination name, the exact Block, and the Floor level clearly.
   - Set "destination" to the matched destination name or ID.
   - Set "building" in entities to the block (e.g. "Block B").
5. When user asks "when it open", "what time", "hours", or OPENING_HOURS:
   - Resolve "it" to the previously discussed location from context.
   - Provide the opening hours for that location.
6. Understand both English and Malay terms:
   - "makmal" = lab, "bilik kuliah" = lecture room, "teater" = theatre, "bengkel" = workshop, "pintu masuk" / "lobi" = entrance/lobby.
7. NAVIGATION COMMANDS ("bring me", "can you bring me", "take me to", "lead me", "guide me", "show me the way", "what good jalan to follow"):
   - The user is asking for walking guidance or navigation to a destination in FTMK.
   - NEVER interpret "bring me" as physical delivery or fetching objects!
   - Classify as GUIDANCE_REQUEST.
   - If a destination is mentioned (e.g. "bring me to food area", "bring me to AI lab"), set "destination" to that location.
   - If no destination is specified (e.g. "can you bring me", "bring me there"), resolve "destination" from the previous context.
8. AFFIRMATIONS & DIRECTION CONFIRMATIONS ("yes", "sure", "yes sure", "yes susre", "ok", "please", "yes please"):
   - When the user answers affirmatively to an offer of walking directions, classify as GUIDANCE_REQUEST and set "destination" to the previously discussed location from context.
9. ORIGIN-TO-DESTINATION & ROUTE COMMANDS ("short path from X to Y", "shortest path from X to Y", "from X to Y", "route between X and Y", "what good jalan from X to Y"):
   - Classify as GUIDANCE_REQUEST.
   - Set "destination" to the target destination (Y).
   - Set "building" to the block where Y is located.
10. FACULTY & CAMPUS OVERVIEW ("what have in ftmk", "in ftmk what facilitity haver", "can you give information about ftmk", "apa ada kat ftmk"):
   - Classify as FACILITY_INFO.
   - Summarize the 5 main interconnected blocks (Blocks A-E across Levels 1-4) and main facilities (labs, lecture rooms, seminar halls, food at lobby, C-ACT).
   - Set "destination": null.
11. PAIRWISE PROXIMITY COMPARISONS ("is X near Y", "X near with Y", "X near Y?"):
   - If one of the rooms does NOT exist in FTMK (e.g. 'kernel room'), state clearly that it does not exist in FTMK, explain where the valid room is, and set destination to the valid room.
   - If both exist, specify whether they are on the same floor/block or different blocks.

ALLOWED INTENTS:
The system must classify each user message into one of the following intents:
1. GREETING
2. LOCATION_QUERY
3. GUIDANCE_REQUEST
4. FACILITY_INFO
5. OPENING_HOURS
6. GENERAL_HELP
7. DESTINATION_RECOMMENDATION

ENTITY RULES:
1. destination: A specific place mentioned by the user or identified from context.
2. category: A general type or purpose (e.g. laboratory, lecture_hall, studio, facility, meeting_room).
3. building: Block A, Block B, Block C, Block D, or Block E.

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
4. "reply" must contain the natural-language response to the user in English.
5. "destination" should contain the identified destination when applicable. Otherwise, return null.
6. Return valid JSON only. Do not add markdown fences or explanations outside the JSON."""

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

        # Parse and validate JSON
        result = self._parse_response(raw_response)

        # Store clean JSON in history so subsequent turns never inherit formatting errors
        clean_content = json.dumps({
            "intent": result.get("intent", "GENERAL_HELP"),
            "entities": result.get("entities", {}),
            "reply": result.get("reply", ""),
            "destination": result.get("destination"),
        })
        self._history.append({"role": "assistant", "content": clean_content})

        # Cap history to avoid infinite growth (system prompt + last 12 turns)
        if len(self._history) > 13:
            self._history = [self._history[0]] + self._history[-12:]

        # Update internal context
        self._update_context(result.get("entities", {}))

        # Attach internal debug fields
        result["_context"] = dict(self._context)

        # Build handoff payload for navigation intents
        if result.get("intent") in {"GUIDANCE_REQUEST", "DESTINATION_RECOMMENDATION"}:
            result["_handoff"] = self._build_handoff(result)

        return result

    def record_turn(self, user_message: str, assistant_reply: str, entities: Optional[dict] = None):
        """Record an externally handled conversation turn so LLM context remains synchronized."""
        import json
        self._history.append({"role": "user", "content": user_message})
        dest_val = (entities or {}).get("destination")
        payload = {
            "intent": "FACILITY_INFO" if any(w in assistant_reply for w in ["Food", "Library", "Opening Hours"]) else "GUIDANCE_REQUEST",
            "entities": entities or {"destination": dest_val, "category": None, "building": None},
            "reply": assistant_reply,
            "destination": dest_val,
        }
        self._history.append({"role": "assistant", "content": json.dumps(payload)})
        if entities:
            self._update_context(entities)

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
        if not reply or not str(reply).strip() or str(reply).strip() in ("", "null", "None"):
            for alt in ["response", "message", "text", "content", "answer"]:
                alt_val = data.get(alt)
                if alt_val and str(alt_val).strip() not in ("", "null", "None"):
                    reply = str(alt_val).strip()
                    break

        if not reply or not str(reply).strip() or str(reply).strip() in ("", "null", "None"):
            if intent == "GREETING":
                reply = "Hello! Welcome to FTMK. How can I assist you today?"
            else:
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
        """Return a safe fallback result when parsing fails, recovering raw reply if available."""
        clean_raw = re.sub(r"<think>.*?</think>", "", raw_reply, flags=re.DOTALL).strip()
        clean_raw = re.sub(r"```(?:json)?\s*", "", clean_raw).strip().rstrip("`").strip()
        # If the LLM returned a coherent conversational response without JSON structure, use it directly!
        if clean_raw and not clean_raw.startswith("{") and len(clean_raw) > 5:
            return {
                "intent": "GENERAL_HELP",
                "entities": {"destination": None, "category": None, "building": None},
                "reply": clean_raw,
                "destination": None,
                "_error": None,
                "_raw": raw_reply,
            }

        return {
            "intent": "GENERAL_HELP",
            "entities": {"destination": None, "category": None, "building": None},
            "reply": "I'm sorry, I had trouble understanding that. Could you please rephrase?",
            "destination": None,
            "_error": error_msg,
            "_raw": raw_reply,
        }
