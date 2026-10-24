import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure the AI module directory and repo root are in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parents[2]
AI_DIR = REPO_ROOT / "AI"

for path in [str(AI_DIR), str(REPO_ROOT)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import NLPModule
try:
    from nlp_module import NLPModule
except ImportError:
    try:
        from AI.nlp_module import NLPModule
    except ImportError:
        NLPModule = None

# Import CampusNLP preprocessor & entity resolver
try:
    from campus_nlp import CampusNLP
except ImportError:
    try:
        from AI.campus_nlp import CampusNLP
    except ImportError:
        CampusNLP = None

# Import backend knowledge base and routing
from backend.knowledge_base.repository import KnowledgeBaseRepository
from backend.services.routing_service import RoutingService

# Import recommendation engine
try:
    from AI.recommendation import RecommendationEngine
except ImportError:
    try:
        from recommendation import RecommendationEngine
    except ImportError:
        RecommendationEngine = None


class AssistantService:
    """
    Intelligent Assistant Service integrating Member 2's NLPModule (Ollama LLM)
    with campus map routing, knowledge base lookup, and recommendation engine.
    """

    def __init__(self, default_model: Optional[str] = None):
        # Allow model override via OLLAMA_MODEL environment variable or default to llama3.2:3b
        self.default_model = default_model or os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        self._sessions: Dict[str, Any] = {}
        self._session_memory: Dict[str, Dict[str, Any]] = {}
        self.repository = KnowledgeBaseRepository()
        self.routing_service = RoutingService()
        self.recommendation_engine = (
            RecommendationEngine() if RecommendationEngine is not None else None
        )

    def get_or_create_session(self, session_id: str):
        """Retrieve existing NLPModule instance for the session or create a new one."""
        if session_id not in self._sessions:
            if NLPModule is None:
                raise RuntimeError("NLPModule could not be imported from AI/nlp_module.py")
            self._sessions[session_id] = NLPModule(model=self.default_model)
            if session_id not in self._session_memory:
                self._session_memory[session_id] = {
                    "last_destination": None,
                    "last_building": None,
                    "last_category": None,
                    "last_intent": None,
                    "last_topic": None,
                    "awaiting_direction_confirmation": False,
                    "direction_destination": None,
                }
        return self._sessions[session_id]

    def reset_session(self, session_id: str) -> bool:
        """Clear conversation history and context for a specific session."""
        if session_id in self._sessions:
            self._sessions[session_id].reset()
            self._session_memory[session_id] = {
                "last_destination": None,
                "last_building": None,
                "last_category": None,
                "last_intent": None,
                "last_topic": None,
                "awaiting_direction_confirmation": False,
                "direction_destination": None,
            }
            return True
        return False

    def _get_memory(self, session_id: str) -> Dict[str, Any]:
        """Get or initialize memory for session."""
        if session_id not in self._session_memory:
            self._session_memory[session_id] = {
                "last_destination": None,
                "last_building": None,
                "last_category": None,
                "last_intent": None,
                "last_topic": None,
                "awaiting_direction_confirmation": False,
                "direction_destination": None,
            }
        return self._session_memory[session_id]

    @staticmethod
    def _normalize_location_query(text: str) -> str:
        """
        Normalizes colloquial speech, contractions, room abbreviations, and typos
        to canonical names for accurate entity matching.
        """
        s = text.lower().strip()
        # Remove polite filler words and request phrases
        s = re.sub(
            r'\b(can you|could you|please|pls|show me|bring me to|take me to|where is|how to get to|directions to|path to|route to|short path to|walking directions to)\b',
            '',
            s
        ).strip()
        # Contractions & room abbreviations with room numbers
        s = re.sub(r'\bprog(?:ram(?:ming)?)?\s*(?:lab(?:oratory)?)?\s*([1-4])\b', r'programming lab \1', s)
        s = re.sub(r'\bmakmal\s*program(?:ming)?\s*([1-4])\b', r'makmal pengaturcaraan \1', s)
        s = re.sub(r'\bai\s*(?:lab(?:oratory)?)?\s*([1-4])\b', r'ai lab \1', s)
        s = re.sub(r'\b(?:data(?:base)?|db)\s*(?:lab(?:oratory)?)?\s*([1-3])\b', r'database lab \1', s)
        s = re.sub(r'\b(?:soft(?:ware)?\s*eng(?:ineering)?|se)\s*(?:lab(?:oratory)?)?\s*([1-3])\b', r'software engineering lab \1', s)
        s = re.sub(r'\b(?:multi(?:media)?|mm)\s*(?:lab(?:oratory)?)?\s*([1-4])\b', r'multimedia lab \1', s)
        s = re.sub(r'\b(?:net(?:work)?)\s*(?:lab(?:oratory)?)?\s*([1-2])\b', r'network lab \1', s)
        s = re.sub(r'\b(?:lec(?:ture)?\s*room|bilik\s*kuliah|bk)\s*([0-9]{1,2})\b', r'lecture room \1', s)
        s = re.sub(r'\b(?:audio\s*recording|rakaman\s*audio)\s*(?:room)?\s*([1-2])\b', r'audio recording room \1', s)
        # Facilities & common locations
        s = re.sub(r'\brobot(?:ic(?:s)?)?\s*lab\b', r'robotics lab', s)
        s = re.sub(r'\bvr\s*lab\b', r'virtual reality lab', s)
        s = re.sub(r'\bgames?\s*lab\b', r'computer games lab', s)
        s = re.sub(r'\bcommon\s*room\b', r'students common room', s)
        s = re.sub(r'\bdiscussion\s*room\b', r'discussion room', s)
        s = re.sub(r'\bbincang\b', r'discussion room', s)
        s = re.sub(r'\bseminar\s*(?:hall|room)?\b', r'seminar hall', s)
        s = re.sub(r'\bexam\s*hall\b', r'seminar hall', s)
        s = re.sub(r'\bviva\s*(?:room)?\b', r'viva room', s)
        s = re.sub(r'\bmeeting\s*room\b', r'main meeting room', s)
        s = re.sub(r'\bcact\b', r'c-act', s)
        return s

    def _find_location_in_text(self, text: str) -> Optional[Dict]:
        """
        Intelligently scan text for any known campus location name or alias.
        Uses CampusNLP preprocessor, longest-alias-first resolver, and fuzzy matching.
        """
        if CampusNLP:
            loc = CampusNLP.find_location(text, self.repository)
            if loc:
                return loc

        text_clean = text.strip()
        if not text_clean:
            return None

        # 1. Exact match on name or alias
        exact = self.repository.search_by_name(text_clean)
        if exact:
            return exact

        # 2. Check normalized query
        norm = self._normalize_location_query(text_clean)
        if norm and norm != text_clean.lower():
            exact_norm = self.repository.search_by_name(norm)
            if exact_norm:
                return exact_norm

        # 3. Check alias word boundary matching (longest alias first)
        all_locs = sorted(self.repository.get_all(), key=lambda x: len(x["name"]), reverse=True)
        text_lower = text_clean.lower()
        search_texts = [text_lower]
        if norm and norm != text_lower:
            search_texts.append(norm)

        for st in search_texts:
            for loc in all_locs:
                for alias in loc.get("aliases", []):
                    alias_lower = alias.lower()
                    if re.search(r'\b' + re.escape(alias_lower) + r'\b', st):
                        return loc

        # 4. Check full names and split "/" parts
        for st in search_texts:
            for loc in all_locs:
                loc_name_lower = loc["name"].lower()
                if loc_name_lower in st:
                    return loc
                if "/" in loc["name"]:
                    parts = [p.strip().lower() for p in loc["name"].split("/")]
                    for part in parts:
                        if part in st:
                            return loc

        # 5. Direct Block gateway mapping if user mentions an entire block
        block_match = re.search(r'\bblock\s+([a-e])\b', text_lower)
        if block_match:
            b_letter = block_match.group(1).upper()
            gateways = {
                "A": "MAIN_ENTRANCE",
                "B": "B_B_L1_PROGRAMMING_LAB_1",
                "C": "B_C_L1_SOFTWARE_ENGINEERING_LAB_1",
                "D": "B_D_L1_STUDENTS_COMMON_ROOM",
                "E": "B_E_L1_GAME_ARENA",
            }
            if b_letter in gateways:
                gw = self.repository.get(gateways[b_letter])
                if gw:
                    return gw

        # 6. Fallback repository keyword search
        results = self.repository.search(text_clean)
        if results:
            return results[0]
        if norm and norm != text_clean:
            results_norm = self.repository.search(norm)
            if results_norm:
                return results_norm[0]

        return None

    def _is_affirmative(self, message: str) -> bool:
        """
        Detects whether user's message is an affirmation / confirmation to a previous direction offer.
        Handles casual slang, typos ("yes susre"), and short confirmations.
        """
        msg = re.sub(r'[^\w\s]', '', message.lower()).strip()
        words = msg.split()
        if not words:
            return False

        # Common single affirmative tokens or typos
        aff_tokens = {
            "yes", "y", "ya", "yea", "yeah", "yep", "yup", "yess", "yesss",
            "sure", "susre", "shure", "sue", "ok", "okay", "okeh", "k", "kk",
            "alright", "allright", "please", "pls", "plz", "ples", "boleh", "nak",
            "haah", "haa", "ha", "jom", "proceed", "go", "can", "wants", "want"
        }

        # Multi-word exact affirmations
        exact_phrases = {
            "yes sure", "yes susre", "yes please", "yes pls", "yes ples", "yes please bring me",
            "yes please take me", "sure please", "sure thing", "of course",
            "definitely", "why not", "go ahead", "all right", "can you",
            "please do", "yes i would", "yes i want", "yes bring me", "yes guide me",
            "ya tolong", "boleh tolong", "haah nak", "jom pergi", "yes tolong",
            "yes show me", "yes directions", "sure directions", "yes walk", "yes walking",
            "show direction", "show directions", "show me directions", "show me direction"
        }

        if msg in exact_phrases:
            return True

        if len(words) <= 5:
            if words[0] in aff_tokens:
                return True
            if any(w in aff_tokens for w in words) and any(
                w in {"bring", "take", "guide", "lead", "show", "direct", "directions", "way", "walk", "walking", "path"}
                for w in words
            ):
                return True

        return False

    def _is_negative(self, message: str) -> bool:
        """Detects whether user is explicitly declining or canceling a direction offer."""
        msg = re.sub(r'[^\w\s]', '', message.lower()).strip()
        negatives = {
            "no", "nope", "nah", "no thanks", "no thank you", "dont", "don't",
            "cancel", "stop", "nevermind", "never mind", "takpe", "tak nak",
            "xnak", "tak payah", "tak mau", "not now"
        }
        return msg in negatives or msg.startswith("no ") or msg.startswith("tak ")

    def _is_navigation_command(self, message: str) -> bool:
        """Detects whether user is explicitly commanding navigation / walking guidance."""
        if CampusNLP and CampusNLP.is_navigation_intent(message):
            return True
        msg_lower = message.lower().strip()
        patterns = [
            r'\bbring me\b',
            r'\bcan you bring me\b',
            r'\bcould you bring me\b',
            r'\btake me\b',
            r'\bcan you take me\b',
            r'\bguide me\b',
            r'\blead me\b',
            r'\bshow me\b',
            r'\bshow me the way\b',
            r'\bshow the way\b',
            r'\bshow direction\b',
            r'\bshow directions\b',
            r'\bshow the direction\b',
            r'\bshow the directions\b',
            r'\bwalking directions\b',
            r'\bdirections to\b',
            r'\bhow to get to\b',
            r'\bhow do i get to\b',
            r'\bhow can i get to\b',
            r'\bhow to go\b',
            r'\bhow do i go\b',
            r'\bhow do i walk\b',
            r'\bhow can i walk\b',
            r'\bwalk to\b',
            r'\broute to\b',
            r'\bnearest path\b',
            r'\bshortest path\b',
            r'\bshort path\b',
            r'\bshort part\b',
            r'\bclosest path\b',
            r'\bfastest (?:path|route|way)\b',
            r'\bquickest (?:path|route|way)\b',
            r'\bshow (?:me )?(?:short |shortest |nearest )?(?:path|route)\b',
            r'\bjalan ke\b',
            r'\bnak ke\b',
            r'\bbawa saya\b',
            r'\btunjukkan jalan\b',
            r'\btolong pandu\b',
        ]
        return any(re.search(p, msg_lower) for p in patterns)

    def _extract_origin_and_destination(
        self, message: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Extracts both an explicit origin and destination from natural human phrasing.
        Uses CampusNLP for typo-resilient semantic slot extraction.
        """
        if CampusNLP:
            orig, dest = CampusNLP.extract_origin_and_destination(message, self.repository)
            if orig and dest:
                return orig, dest

        msg_clean = message.strip().rstrip("?.!,")

        patterns = [
            # 1. "from <origin> to <dest>" / "dari <origin> ke <dest>"
            r'\b(?:from|dari)\s+(.+?)\s+(?:to|ke|towards|sampai)\s+(.+)',
            # 2. "between <origin> and <dest>" / "antara <origin> dan <dest>"
            r'\b(?:between|antara)\s+(.+?)\s+(?:and|dan|with|dengan)\s+(.+)',
            # 3. "<dest> from <origin>" / "how to get/go to <dest> from <origin>"
            r'(?:how\s+(?:to|do\s+i|can\s+i)\s+(?:get|go|walk)\s+to|directions?\s+to|path\s+to|route\s+to|way\s+to|navigate\s+to|\bto|\bke|\btowards)\s+(.+?)\s+(?:from|dari)\s+(.+)',
            # 4. Direct "<origin> to <dest>" without "from" prefix
            r'^(?:can\s+you\s+)?(?:show\s+(?:me\s+)?)?(?:short\s+|shortest\s+|nearest\s+)?(?:path\s+|route\s+)?(?:from\s+)?(.+?)\s+(?:to|ke|towards)\s+(.+)$',
        ]

        for idx, pattern in enumerate(patterns):
            match = re.search(pattern, msg_clean, re.IGNORECASE)
            if match:
                g1, g2 = match.group(1).strip(), match.group(2).strip()
                if idx == 2:
                    dest_cand, orig_cand = g1, g2
                else:
                    orig_cand, dest_cand = g1, g2

                # Clean polite, navigational, or filler words
                clean_re = r'\b(please|pls|can you|can i|could you|show me|tell me|give me|short|shortest|nearest|fastest|quickest|path|route|way|walk|how to get to|how do i get to|how to go to|how do i go to|how to get|how do i get|how to go|how to|go to|get to|go|get)\b'
                orig_clean = re.sub(clean_re, '', orig_cand, flags=re.I).strip()
                dest_clean = re.sub(clean_re, '', dest_cand, flags=re.I).strip()

                orig_loc = self._find_location_in_text(orig_clean) or self._find_location_in_text(orig_cand)
                dest_loc = self._find_location_in_text(dest_clean) or self._find_location_in_text(dest_cand)

                if orig_loc and dest_loc:
                    return orig_loc, dest_loc

        return None, None

    def _find_nearest_facility(
        self, current_loc: str, category_or_kw: str = "toilet"
    ) -> Tuple[Optional[Dict[str, Any]], int, Optional[Dict[str, Any]]]:
        """
        Dynamically calculates the shortest path from current_loc to all matching
        facilities (e.g. toilets) and returns the closest one.
        """
        candidates = [
            loc for loc in self.repository.get_all()
            if loc.get("category") == category_or_kw
            or any(category_or_kw in k.lower() for k in loc.get("keywords", []))
            or any(category_or_kw in a.lower() for a in loc.get("aliases", []))
        ]
        if not candidates:
            return None, 0, None

        best_loc = None
        best_dist = float("inf")
        best_route = None

        for loc in candidates:
            loc_id = loc["id"]
            if current_loc == loc_id:
                return loc, 0, {"status": "success", "total_distance": 0, "instructions": ["You are right outside the facility."]}

            route = self.routing_service.get_shortest_route(current_loc, loc_id)
            if "status" in route and route["status"] == "success":
                dist = route.get("total_distance", float("inf"))
                if dist < best_dist:
                    best_dist = dist
                    best_loc = loc
                    best_route = route

        if best_loc:
            return best_loc, best_dist, best_route

        return candidates[0], 0, None

    def _build_walking_directions_response(
        self, current_loc: str, dest_loc: Dict[str, Any], extra_tip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Builds walking directions response.
        If user is already at the destination, returns a human-friendly arrival note instead
        of failing with 'cannot route to same place'.
        """
        dest_id = dest_loc["id"]
        dest_name = dest_loc["name"]
        bld = dest_loc.get("building", "FTMK")
        flr = dest_loc.get("floor", 1)

        # 1. User is ALREADY at the destination
        if current_loc == dest_id:
            if dest_id == "MAIN_ENTRANCE" or "food" in (dest_loc.get("purposes") or []):
                reply = (
                    f"📍 **You are already at the Main Entrance / Lobby (Block A, Level 1)!**\n\n"
                    f"The food vendors selling **Nasi Lemak**, **Karipap & Pau**, **Local Kuih**, snacks, "
                    f"and cold drinks are set up right here in the lobby area near the entrance. Enjoy your food! 🥪🥤"
                )
            else:
                reply = (
                    f"📍 **You are already at {dest_name} ({bld}, Level {flr})!**\n\n"
                    f"You have arrived at your destination, so no walking directions are needed. "
                    f"Let me know if you need directions to anywhere else!"
                )

            return {
                "reply": reply,
                "intent": "GUIDANCE_REQUEST",
                "destination_id": dest_id,
                "confidence": 1.0,
                "entities": {
                    "destination": dest_name,
                    "category": dest_loc.get("category"),
                    "building": bld,
                },
                "handoff": {
                    "type": "ARRIVED",
                    "start_id": current_loc,
                    "destination_id": dest_id,
                    "destination_name": dest_name,
                    "message": "You are already at your destination.",
                },
                "route_info": None,
                "recommendations": None,
                "error": None,
            }

        # 2. Compute Dijkstra shortest route
        route_calc = self.routing_service.get_shortest_route(current_loc, dest_id)
        if "status" in route_calc and route_calc["status"] == "success":
            dist = route_calc.get("total_distance", 0)
            start_name = route_calc.get("start", current_loc)
            steps_formatted = "\n".join(
                f"{i+1}. {step}" for i, step in enumerate(route_calc.get("instructions", []))
            )
            tip_text = f"\n\n{extra_tip}" if extra_tip else ""
            reply = (
                f"🚶‍♂️ **Walking Directions to {dest_name} ({bld}, Level {flr}) from {start_name} ({dist}m):**\n\n"
                f"{steps_formatted}"
                f"{tip_text}\n\n"
                f"Feel free to ask if you need directions to anywhere else!"
            )
            handoff = {
                "type": "NAVIGATION",
                "start_id": current_loc,
                "destination_id": dest_id,
                "destination_name": dest_name,
                "map_url": f"/map?start={current_loc}&dest={dest_id}",
                "route": route_calc,
            }
            route_info = route_calc
        else:
            reply = (
                f"📍 **{dest_name}** is located in **{bld}, Level {flr}**.\n"
                f"(Walking path currently unavailable from {current_loc})."
            )
            handoff = {
                "type": "NAVIGATION_UNAVAILABLE",
                "start_id": current_loc,
                "destination_id": dest_id,
                "error": route_calc.get("error", "Route could not be calculated"),
            }
            route_info = None

        return {
            "reply": reply,
            "intent": "GUIDANCE_REQUEST",
            "destination_id": dest_id,
            "confidence": 1.0,
            "entities": {
                "destination": dest_name,
                "category": dest_loc.get("category"),
                "building": bld,
            },
            "handoff": handoff,
            "route_info": route_info,
            "recommendations": None,
            "error": None,
        }

    def _record_nlp_turn(
        self, session_id: str, user_msg: str, bot_reply: str, entities: Optional[Dict] = None
    ):
        """Record turn in NLP module session so Ollama LLM conversation context remains synchronized."""
        try:
            if session_id in self._sessions:
                nlp = self._sessions[session_id]
                if hasattr(nlp, "record_turn"):
                    nlp.record_turn(user_msg, bot_reply, entities)
        except Exception:
            pass

    def _handle_block_query(
        self, message: str, session_mem: Dict[str, Any], current_loc: str
    ) -> Optional[str]:
        """
        Handles block-specific queries like "which block", "what blocks are there",
        or "what is in Block B".
        """
        msg_lower = message.lower().strip()

        # 1. Check if user is asking about a specific block (e.g. "what is in Block B" or "Block C")
        block_match = re.search(r'\bblock\s+([a-e])\b', msg_lower, re.IGNORECASE)
        if block_match:
            block_letter = block_match.group(1).upper()
            block_name = f"Block {block_letter}"
            locs = self.repository.filter_by_building(block_name)
            if locs:
                by_floor: Dict[int, List[str]] = {}
                for l in locs:
                    fl = l.get("floor", 1)
                    by_floor.setdefault(fl, []).append(l["name"])

                lines = [f"🏛️ **Facilities in {block_name}:**\n"]
                for fl in sorted(by_floor.keys()):
                    places = " • ".join(by_floor[fl])
                    lines.append(f"**Level {fl}:**\n{places}\n")

                lines.append("Feel free to ask for directions or details about any of these rooms!")
                return "\n".join(lines)

        # 2. Check if user is asking general "which block" / "what block"
        is_block_inquiry = any(phrase in msg_lower for phrase in [
            "which block", "what block", "what blocks", "list blocks", "show blocks",
            "tell me about the blocks", "which building", "what building", "blocks in ftmk",
            "ada blok apa", "blok mana", "senarai blok"
        ]) or msg_lower in (
            "which block?", "which block", "what block?", "what block",
            "blok mana?", "blok mana", "block?", "building?"
        )

        if is_block_inquiry:
            last_dest = session_mem.get("last_destination")
            if last_dest:
                dest_name = last_dest["name"]
                bld = last_dest.get("building", "FTMK")
                flr = last_dest.get("floor", 1)
                session_mem["direction_destination"] = last_dest
                session_mem["awaiting_direction_confirmation"] = True
                return (
                    f"📍 **{dest_name}** is located in **{bld}, Level {flr}**.\n\n"
                    f"Would you like walking directions from {current_loc}?"
                )
            else:
                return (
                    "🏛️ **FTMK Campus consists of 5 main connected blocks:**\n\n"
                    "• **Block A**: Main Entrance / Lobby (L1), C-ACT, Discussion Rooms (L2-L3), Seminar Hall & Main Meeting Room (L4)\n"
                    "• **Block B**: Lecture Rooms 6 & 7, Bilik VIVA, Programming Labs 1 & 2 (L1), AI Labs 1-4 (L2), Robotics Lab & BITI Workshop (L3), Lecture Rooms 15 & 16 (L3-L4)\n"
                    "• **Block C**: Software Engineering Labs 1-3, Lecture Rooms 1-5 (L1), Database Labs 1-3 (L2), Systems & Network Labs (L3), Programming Labs 3 & 4 (L4)\n"
                    "• **Block D**: Metaverse Studio, Students' Common Room (L1), Computer Games & Multimedia Labs (L2-L3), Mini Theatre & VR Lab (L3), Audio Recording Studios (L3)\n"
                    "• **Block E**: Game Arena (L1), Cybersecurity Competence Center, CCNA & Fiber Optic Labs (L2), Wireless & Cloud Computing Labs (L3)\n\n"
                    "Which block or facility would you like to visit?"
                )

        return None

    def _handle_special_facilities(
        self, message: str, session_mem: Dict[str, Any], current_loc: str
    ) -> Optional[str]:
        """
        Deterministic handling for special queries:
        1. Library queries (FTMK has no internal library)
        2. Food / Cafe queries (food vendors at Lobby / Main Entrance)
        3. Opening hours multi-turn context
        """
        msg_lower = message.lower().strip()

        # -------------------------------------------------------------
        # 1. Opening hours multi-turn check ("when it open", "opening hours", etc.)
        # -------------------------------------------------------------
        is_hours_query = any(phrase in msg_lower for phrase in [
            "when it open", "when does it open", "when is it open", "what time does it open",
            "what time it open", "what time is it open", "opening hours", "opening hour",
            "open hours", "operating hours", "when open", "bila buka", "waktu operasi",
            "pukul berapa buka", "waktu buka"
        ])

        if is_hours_query:
            # Check if user previously discussed the library
            if session_mem.get("last_topic") == "library" or any(w in msg_lower for w in ["lib", "library", "perpustakaan"]):
                c_act_loc = self.repository.get("C-ACT") or self.repository.search_by_name("C-ACT")
                session_mem["direction_destination"] = c_act_loc
                session_mem["awaiting_direction_confirmation"] = True
                return (
                    "🕒 **Perpustakaan Laman Hikmah (Main UTeM Library) Opening Hours:**\n\n"
                    "• **Monday – Friday:** 8:30 AM – 10:00 PM\n"
                    "• **Saturday – Sunday:** 9:00 AM – 5:00 PM (open during revision & exam weeks)\n\n"
                    "*(Note: The main library is located at the central UTeM campus outside FTMK).*\n\n"
                    "For study areas inside FTMK, **C-ACT** (Block A, Level 1) and **Discussion Rooms** are accessible during regular campus hours (8:00 AM – 6:00 PM).\n\n"
                    "Would you like walking directions to C-ACT?"
                )

            # Check if user previously discussed food
            if session_mem.get("last_topic") == "food":
                main_ent = self.repository.get("MAIN_ENTRANCE")
                session_mem["last_destination"] = main_ent
                session_mem["direction_destination"] = main_ent
                session_mem["awaiting_direction_confirmation"] = True
                return (
                    "🕒 **Lobby Food Vendors Operating Hours:**\n\n"
                    "• **Weekdays (Monday – Friday):** 7:30 AM – 2:00 PM\n"
                    "• **Weekends:** Closed\n\n"
                    "You can grab Nasi Lemak, Karipap, Pau, and drinks at the Main Entrance (Block A, Level 1).\n\n"
                    "Would you like walking directions to the Main Entrance?"
                )

            # Check if active destination in session memory
            last_dest = session_mem.get("last_destination")
            if last_dest:
                dest_name = last_dest["name"]
                bld = last_dest.get("building", "FTMK")
                flr = last_dest.get("floor", 1)
                hours = last_dest.get("opening_hours")
                session_mem["direction_destination"] = last_dest
                session_mem["awaiting_direction_confirmation"] = True
                if hours and isinstance(hours, dict):
                    wk = hours.get("weekday", "08:00-18:00")
                    we = hours.get("weekend", "closed")
                    return (
                        f"🕒 **Opening Hours for {dest_name} ({bld}, Level {flr}):**\n\n"
                        f"• **Weekdays:** {wk}\n"
                        f"• **Weekends:** {we}\n\n"
                        f"Would you like walking directions from {current_loc}?"
                    )
                else:
                    return (
                        f"🕒 **{dest_name}** ({bld}, Level {flr}) follows standard FTMK academic hours:\n\n"
                        f"• **Weekdays (Monday – Friday):** 8:00 AM – 6:00 PM\n"
                        f"• **Weekends:** Closed\n\n"
                        f"Would you like walking directions from {current_loc}?"
                    )

        # -------------------------------------------------------------
        # 2. Library queries ("where lib", "library", "perpustakaan")
        # -------------------------------------------------------------
        is_library_query = re.search(r'\b(lib|library|perpustakaan|reading room)\b', msg_lower)
        if is_library_query:
            session_mem["last_topic"] = "library"
            c_act_loc = self.repository.get("C-ACT") or self.repository.search_by_name("C-ACT")
            session_mem["direction_destination"] = c_act_loc
            session_mem["awaiting_direction_confirmation"] = True
            return (
                "ℹ️ **FTMK does not have a library inside the building.**\n\n"
                "• The main university library (**Perpustakaan Laman Hikmah**) is located at the central UTeM campus.\n"
                "• If you need a study area inside FTMK, you can visit:\n"
                "  - **C-ACT** (Block A, Level 1)\n"
                "  - **Bilik Bincang / Discussion Room** (Block A, Level 2)\n"
                "  - **Bilik Umum Pelajar / Students' Common Room** (Block D, Level 1)\n\n"
                "Would you like walking directions to C-ACT (the main study area in FTMK) or opening hours for the main library?"
            )

        # -------------------------------------------------------------
        # 3. Food / Cafe / Snack queries ("karipap", "nasi lemak", "pau", "cafe", etc.)
        # -------------------------------------------------------------
        is_food_query = re.search(
            r'\b(food|cafe|cafeteria|canteen|nasi lemak|karipap|pau|makan|hungry|lapar|breakfast|sarapan|snacks|snack|kuih|drinks)\b',
            msg_lower
        )
        if is_food_query:
            session_mem["last_topic"] = "food"
            main_ent = self.repository.get("MAIN_ENTRANCE")
            if main_ent:
                session_mem["last_destination"] = main_ent
                session_mem["direction_destination"] = main_ent
                session_mem["last_building"] = main_ent.get("building")

            # If user is specifically commanding navigation ("bring me to food", "directions to food area"),
            # do NOT return the introductory overview text; let handle_query route directly!
            if self._is_navigation_command(msg_lower):
                return None

            session_mem["awaiting_direction_confirmation"] = True

            if current_loc == "MAIN_ENTRANCE":
                return (
                    "🍴 **Food & Snacks at FTMK:**\n\n"
                    "While FTMK does not have a dedicated cafeteria inside the building, local food vendors are located right here at the **Main Entrance / Lobby (Block A, Level 1)**!\n\n"
                    "They sell breakfast and snacks, including:\n"
                    "• **Nasi Lemak**\n"
                    "• **Karipap & Pau**\n"
                    "• **Local Kuih, Snacks & Cold Drinks**\n\n"
                    "Operating hours are typically **7:30 AM – 2:00 PM on weekdays**.\n"
                    "Since you are already at the Main Entrance, the vendor tables are set up right here in the lobby area near the entrance! 🥪🥤"
                )

            return (
                "🍴 **Food & Snacks at FTMK:**\n\n"
                "While FTMK does not have a dedicated cafeteria inside the building, local food vendors at the **Main Entrance / Lobby (Block A, Level 1)** sell breakfast and snacks, including:\n"
                "• **Nasi Lemak**\n"
                "• **Karipap & Pau**\n"
                "• **Local Kuih, Snacks & Cold Drinks**\n\n"
                "Operating hours are typically **7:30 AM – 2:00 PM on weekdays**.\n\n"
                "Would you like walking directions to the Main Entrance?"
            )

        # -------------------------------------------------------------
        # 4. Toilet / Restroom / Tandas queries ("where the toilet", "nearest toilet", etc.)
        # -------------------------------------------------------------
        is_toilet_query = re.search(
            r'\b(toilet|toilets|restroom|restrooms|washroom|washrooms|tandas|bilik air|jamban|lavatory|wc)\b',
            msg_lower
        )
        if is_toilet_query:
            session_mem["last_topic"] = "toilet"
            nearest_toilet, dist, route = self._find_nearest_facility(current_loc, "toilet")
            if nearest_toilet:
                session_mem["last_destination"] = nearest_toilet
                session_mem["direction_destination"] = nearest_toilet
                session_mem["last_building"] = nearest_toilet.get("building")

                # If user specifically commanded navigation ("bring me to toilet", "show direction to toilet")
                # bypass overview and let handle_query route directly!
                if self._is_navigation_command(msg_lower):
                    return None

                session_mem["awaiting_direction_confirmation"] = True
                t_bld = nearest_toilet.get("building", "FTMK")
                t_flr = nearest_toilet.get("floor", 1)

                if current_loc == nearest_toilet["id"] or dist == 0:
                    return (
                        f"🚻 **Nearest Toilet Facility:**\n\n"
                        f"You are right outside the **{t_bld}, Level {t_flr} Restroom**!\n"
                        f"• **Facilities:** Male, Female & Accessible (OKU) Restrooms\n"
                        f"• **Hours:** Open 24/7"
                    )

                return (
                    f"🚻 **Nearest Toilet Facility:**\n\n"
                    f"The closest restroom to you is located at **{t_bld}, Level {t_flr}** "
                    f"(approximately **{dist}m** away).\n"
                    f"• **Facilities:** Male & Female Restrooms\n"
                    f"• **Hours:** Available 24/7\n\n"
                    f"Would you like walking directions to the {t_bld} Level {t_flr} Restroom?"
                )

        return None

    def _sanitize_reply_language(self, reply: str) -> str:
        """
        Detects if Ollama hallucinated in Indonesian / Malay when the user asked in English,
        and sanitizes it into clean English.
        """
        if not reply:
            return reply

        # Hallucination markers from small models
        indo_markers = [
            "perpustakaan fakultas", "fakultas informasi", "anda dapat",
            "naik escalator", "terletak di", "sebelah kiri", "sumber daya",
            "jika anda tidak dapat", "bimbingan lebih lanjut", "koleksi buku"
        ]

        reply_lower = reply.lower()
        if any(marker in reply_lower for marker in indo_markers):
            # Replace hallucinated library / escalator response
            return (
                "ℹ️ **FTMK does not have a library or escalators inside the building.**\n\n"
                "• The main university library (**Perpustakaan Laman Hikmah**) is located at the central UTeM campus.\n"
                "• Within FTMK, study rooms are available at:\n"
                "  - **C-ACT** (Block A, Level 1)\n"
                "  - **Discussion Room** (Block A, Level 2)\n"
                "  - **Students' Common Room** (Block D, Level 1)\n\n"
                "Would you like walking directions to any of these locations?"
            )

        return reply

    async def handle_query(
        self, session_id: str, message: str, current_location_id: str = ""
    ) -> Dict[str, Any]:
        """
        Processes user natural language input via NLPModule.
        Enriches output with:
        - Real location lookup from KnowledgeBaseRepository
        - Calculated navigation path via RoutingService
        - AI destination ranking via RecommendationEngine
        - Conversational block, facility, and opening hours memory
        """
        session_id = session_id or "default"
        current_loc = (current_location_id or "").strip() or "MAIN_ENTRANCE"
        session_mem = self._get_memory(session_id)

        # Step 0: Check for Negative Response ("no", "no thanks", "takpe", etc.)
        if self._is_negative(message) and session_mem.get("awaiting_direction_confirmation"):
            session_mem["awaiting_direction_confirmation"] = False
            reply_text = "No problem! Let me know if you need help with anything else in FTMK."
            self._record_nlp_turn(session_id, message, reply_text)
            return {
                "reply": reply_text,
                "intent": "GENERAL_HELP",
                "destination_id": None,
                "confidence": 1.0,
                "entities": {"destination": None, "category": None, "building": None},
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "session_id": session_id,
                "error": None,
            }

        # Step 0.1: Check for explicit Origin-to-Destination routing ("from A to B", "between A and B")
        orig_match, dest_match = self._extract_origin_and_destination(message)
        if orig_match and dest_match:
            orig_id = orig_match["id"]
            dest_id = dest_match["id"]
            orig_name = orig_match["name"]
            dest_name = dest_match["name"]
            orig_bld = orig_match.get("building", "FTMK")
            orig_flr = orig_match.get("floor", 1)
            dest_bld = dest_match.get("building", "FTMK")
            dest_flr = dest_match.get("floor", 1)

            session_mem["last_destination"] = dest_match
            session_mem["direction_destination"] = dest_match
            session_mem["last_building"] = dest_bld
            session_mem["last_topic"] = dest_match.get("category")
            session_mem["awaiting_direction_confirmation"] = False

            if orig_id == dest_id:
                reply_text = f"📍 **{orig_name}** is already at your starting point! No walking needed."
                route_calc = None
                handoff = {
                    "type": "ARRIVED",
                    "start_id": orig_id,
                    "destination_id": dest_id,
                    "destination_name": dest_name,
                }
            else:
                route_calc = self.routing_service.get_shortest_route(orig_id, dest_id)
                if "status" in route_calc and route_calc["status"] == "success":
                    dist = route_calc.get("total_distance", 0)
                    steps_formatted = "\n".join(
                        f"{i+1}. {step}" for i, step in enumerate(route_calc.get("instructions", []))
                    )
                    reply_text = (
                        f"🚶‍♂️ **Nearest Walking Path from {orig_name} ({orig_bld}, Level {orig_flr}) "
                        f"to {dest_name} ({dest_bld}, Level {dest_flr}) ({dist}m):**\n\n"
                        f"{steps_formatted}\n\n"
                        f"Feel free to ask if you need directions to anywhere else!"
                    )
                    handoff = {
                        "type": "NAVIGATION",
                        "start_id": orig_id,
                        "start_name": orig_name,
                        "destination_id": dest_id,
                        "destination_name": dest_name,
                        "map_url": f"/map?start={orig_id}&dest={dest_id}",
                        "route": route_calc,
                    }
                else:
                    reply_text = (
                        f"📍 Route from **{orig_name}** to **{dest_name}** is currently unavailable."
                    )
                    handoff = {
                        "type": "NAVIGATION_UNAVAILABLE",
                        "start_id": orig_id,
                        "destination_id": dest_id,
                        "error": route_calc.get("error", "Route could not be calculated"),
                    }

            self._record_nlp_turn(session_id, message, reply_text, {
                "destination": dest_name,
                "category": dest_match.get("category"),
                "building": dest_bld
            })

            return {
                "reply": reply_text,
                "intent": "GUIDANCE_REQUEST",
                "destination_id": dest_id,
                "confidence": 1.0,
                "entities": {
                    "destination": dest_name,
                    "category": dest_match.get("category"),
                    "building": dest_bld,
                },
                "handoff": handoff,
                "route_info": route_calc,
                "recommendations": None,
                "session_id": session_id,
                "error": None,
            }

        # Step 0.5: Check for Affirmative Confirmation or Follow-up Navigation Command
        is_aff = self._is_affirmative(message)
        is_nav = self._is_navigation_command(message)
        direct_loc_check = self._find_location_in_text(message)

        # Did the user say "can you bring me" / "bring me" with NO location, and NO previous destination in memory?
        if is_nav and not direct_loc_check and not session_mem.get("last_destination") and not session_mem.get("direction_destination"):
            reply_text = (
                "I'd be glad to guide you! Where would you like to go? "
                "You can ask for any room, lab, or area in FTMK (such as C-ACT, AI Lab 1, or the food vendors at the lobby)."
            )
            self._record_nlp_turn(session_id, message, reply_text)
            return {
                "reply": reply_text,
                "intent": "GENERAL_HELP",
                "destination_id": None,
                "confidence": 1.0,
                "entities": {"destination": None, "category": None, "building": None},
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "session_id": session_id,
                "error": None,
            }

        # Confirmation / Follow-up direction trigger:
        # User confirmed ("yes", "sure", "susre", "ok") OR requested navigation ("can you bring me", "bring me there")
        if (is_aff or is_nav) and (session_mem.get("awaiting_direction_confirmation") or session_mem.get("last_destination")):
            target_dest = direct_loc_check or session_mem.get("direction_destination") or session_mem.get("last_destination")
            if not target_dest and session_mem.get("last_topic") == "library":
                target_dest = self.repository.get("C-ACT") or self.repository.search_by_name("C-ACT")

            if target_dest:
                session_mem["awaiting_direction_confirmation"] = False
                session_mem["last_destination"] = target_dest
                session_mem["last_building"] = target_dest.get("building")
                session_mem["last_topic"] = target_dest.get("category")

                extra_tip = None
                if target_dest.get("id") == "MAIN_ENTRANCE" or session_mem.get("last_topic") == "food":
                    extra_tip = "Once you arrive at the lobby on Level 1, the food vendors (selling Nasi Lemak, Karipap, Pau, snacks & drinks) are set up right near the entrance!"

                res = self._build_walking_directions_response(current_loc, target_dest, extra_tip)
                res["session_id"] = session_id
                self._record_nlp_turn(session_id, message, res["reply"], res["entities"])
                return res

        # Step 1: Pre-check for Block inquiries ("which block", "what is in block B", etc.)
        block_reply = self._handle_block_query(message, session_mem, current_loc)
        if block_reply:
            entities = {
                "destination": session_mem.get("last_destination", {}).get("name") if session_mem.get("last_destination") else None,
                "category": "building",
                "building": session_mem.get("last_destination", {}).get("building") if session_mem.get("last_destination") else None,
            }
            self._record_nlp_turn(session_id, message, block_reply, entities)
            return {
                "reply": block_reply,
                "intent": "LOCATION_QUERY",
                "destination_id": session_mem.get("last_destination", {}).get("id") if session_mem.get("last_destination") else None,
                "confidence": 1.0,
                "entities": entities,
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "session_id": session_id,
                "error": None,
            }

        # Step 2: Pre-check for Special Facilities & Multi-turn (Library, Food/Cafe, Opening Hours)
        special_reply = self._handle_special_facilities(message, session_mem, current_loc)
        if special_reply:
            entities = {
                "destination": session_mem.get("last_destination", {}).get("name") if session_mem.get("last_destination") else None,
                "category": session_mem.get("last_topic"),
                "building": session_mem.get("last_destination", {}).get("building") if session_mem.get("last_destination") else None,
            }
            self._record_nlp_turn(session_id, message, special_reply, entities)
            return {
                "reply": special_reply,
                "intent": "FACILITY_INFO" if "Food" in special_reply or "Library" in special_reply else "OPENING_HOURS",
                "destination_id": session_mem.get("last_destination", {}).get("id") if session_mem.get("last_destination") else None,
                "confidence": 1.0,
                "entities": entities,
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "session_id": session_id,
                "error": None,
            }

        # Step 3: Try finding a referenced destination in user message
        direct_loc_match = self._find_location_in_text(message)

        # Step 4: Run Ollama NLP processing
        try:
            nlp = self.get_or_create_session(session_id)
            result = nlp.process(message)

            intent = result.get("intent", "GENERAL_HELP")
            entities = result.get("entities") or {
                "destination": None,
                "category": None,
                "building": None,
            }
            raw_dest = result.get("destination") or entities.get("destination")
            category = entities.get("category")
            building = entities.get("building")
            reply = self._sanitize_reply_language(result.get("reply", "I'm here to help."))

        except Exception as exc:
            intent = "GENERAL_HELP"
            entities = {"destination": None, "category": None, "building": None}
            raw_dest = None
            category = None
            building = None
            reply = None

        # Step 5: Resolve Location (priority: direct text match > raw NLP entity > session memory)
        loc_match = direct_loc_match
        if not loc_match and raw_dest:
            loc_match = self.repository.get(raw_dest)
            if not loc_match:
                loc_match = self.repository.search_by_name(raw_dest)
            if not loc_match:
                matches = self.repository.search(raw_dest)
                if matches:
                    loc_match = matches[0]

        # Multi-turn reference resolution: if user says "it", "there", "how to go there"
        msg_lower = message.lower()
        has_pronoun = any(word in msg_lower for word in ["it", "there", "that place", "situ", "sana", "tempat tu"])
        if not loc_match and has_pronoun and session_mem.get("last_destination"):
            loc_match = session_mem["last_destination"]

        # Dynamic nearest toilet resolution: if toilet requested, pick closest to current_loc
        if (loc_match and loc_match.get("category") == "toilet") or re.search(r'\b(toilet|toilets|restroom|restrooms|tandas|washroom|washrooms|wc)\b', msg_lower):
            nearest_t, _, _ = self._find_nearest_facility(current_loc, "toilet")
            if nearest_t:
                loc_match = nearest_t

        # Update session memory if destination resolved
        if loc_match:
            session_mem["last_destination"] = loc_match
            session_mem["last_building"] = loc_match.get("building")
            session_mem["last_topic"] = loc_match.get("category")
            destination_id = loc_match["id"]
        else:
            destination_id = None

        destination_name = loc_match["name"] if loc_match else (raw_dest or "your destination")

        # Step 6: Check if query is asking for guidance / directions
        is_guidance_query = (
            intent == "GUIDANCE_REQUEST"
            or self._is_navigation_command(message)
            or any(kw in msg_lower for kw in [
                "how to get to", "how do i get to", "guide me", "directions to",
                "where is", "take me to", "route to", "jalan ke", "nak ke", "macam mana nak",
                "bring me", "can you bring me", "lead me", "walking directions"
            ])
        )

        route_info = None
        recommendations_list = None
        handoff = None

        # Step 7: Route calculation for GUIDANCE_REQUEST
        if is_guidance_query and destination_id:
            intent = "GUIDANCE_REQUEST"
            extra_tip = None
            if destination_id == "MAIN_ENTRANCE" or session_mem.get("last_topic") == "food":
                extra_tip = "Once you arrive at the lobby on Level 1, the food vendors (selling Nasi Lemak, Karipap, Pau, snacks & drinks) are set up right near the entrance!"

            dir_res = self._build_walking_directions_response(current_loc, loc_match, extra_tip)
            reply = dir_res["reply"]
            route_info = dir_res["route_info"]
            handoff = dir_res["handoff"]
            session_mem["awaiting_direction_confirmation"] = False

        # Step 8: Handle DESTINATION_RECOMMENDATION
        elif intent == "DESTINATION_RECOMMENDATION" or any(kw in msg_lower for kw in ["recommend", "cadang", "where can i", "suggest"]):
            if self.recommendation_engine:
                rec_result = self.recommendation_engine.recommend(
                    query=message,
                    category=category,
                    destination=destination_name if loc_match else raw_dest,
                    building=building,
                )
                recommendations_list = rec_result.get("recommendations", [])
                top_match = rec_result.get("top_match")

                if top_match:
                    destination_id = top_match["destination_id"]
                    matched_obj = self.repository.get(destination_id)
                    if matched_obj:
                        session_mem["last_destination"] = matched_obj
                        session_mem["last_building"] = matched_obj.get("building")

                handoff = {
                    "type": "RECOMMENDATION",
                    "top_match": top_match,
                    "total_found": rec_result.get("total_found", 0),
                    "recommendations": recommendations_list,
                }

                if recommendations_list:
                    recs_text = "\n".join(
                        f"• **{r['name']}** — {r.get('building', '')}, Level {r.get('floor', '')}"
                        for r in recommendations_list[:4]
                    )
                    reply = (
                        f"💡 **Recommended destinations for your request:**\n\n"
                        f"{recs_text}\n\n"
                        f"Ask me for directions to any of these places!"
                    )

        # Step 9: Handle LOCATION_QUERY / FACILITY_INFO with identified destination
        elif loc_match:
            bld = loc_match.get("building", "FTMK")
            flr = loc_match.get("floor", 1)
            desc = loc_match.get("description", "")
            facs = ", ".join(loc_match.get("facilities", [])) if loc_match.get("facilities") else "standard facilities"
            hours = loc_match.get("opening_hours")
            hours_str = f"Weekdays: {hours.get('weekday', 'N/A')}" if hours else "Regular campus hours (8:00 AM – 6:00 PM)"

            session_mem["last_destination"] = loc_match
            session_mem["direction_destination"] = loc_match
            session_mem["awaiting_direction_confirmation"] = True

            reply = (
                f"📍 **{destination_name}**\n"
                f"• **Location:** {bld}, Level {flr}\n"
                f"• **Description:** {desc}\n"
                f"• **Facilities:** {facs}\n"
                f"• **Hours:** {hours_str}\n\n"
                f"Would you like walking directions from {current_loc}?"
            )
            handoff = {
                "type": "LOCATION_INFO",
                "location": loc_match,
            }

        # Step 10: Default / Greeting / General Help
        elif not reply:
            reply = (
                "Hello! I am your FTMK AI Guidance Assistant. "
                "You can ask me for directions to any lab or room, ask which block a facility is in, "
                "or ask for food at the lobby!"
            )

        session_mem["last_intent"] = intent

        return {
            "reply": reply,
            "intent": intent,
            "destination_id": destination_id,
            "confidence": 1.0,
            "entities": {
                "destination": destination_name if loc_match else raw_dest,
                "category": category or (loc_match.get("category") if loc_match else None),
                "building": building or (loc_match.get("building") if loc_match else None),
            },
            "handoff": handoff,
            "route_info": route_info,
            "recommendations": recommendations_list,
            "session_id": session_id,
            "error": None,
        }


# Singleton instance for easy dependency injection
assistant_service = AssistantService()
