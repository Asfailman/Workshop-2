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
            "show direction", "show directions", "show me directions", "show me direction",
            "lead the way", "lets go", "let's go", "take me there", "guide me there",
            "bring it on", "yes please guide me", "alright guide me", "ok show me",
            "lets do it", "let's do it", "show the way", "yes take me", "yes please lead"
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
        msg_lower = message.lower().strip()
        # If user is providing an origin or correction ("no from X", "no to Y", "no I mean X"), it is NOT a decline!
        if re.search(r'\b(?:from|dari|dr|start\s+from|starting\s+from|to|ke|i\s+mean|actually|instead|bukan|maksud\s+saya)\b', msg_lower):
            return False

        msg = re.sub(r'[^\w\s]', '', msg_lower).strip()
        negatives = {
            "no", "nope", "nah", "no thanks", "no thank you", "dont", "don't",
            "cancel", "stop", "nevermind", "never mind", "takpe", "tak nak",
            "xnak", "tak payah", "tak mau", "not now", "tak perlu", "tak pe"
        }
        if msg in negatives:
            return True

        if re.match(r'^(?:no|tak|xnak|tak nak)\s+(?:thanks?|thank\s+you|need|need\s+directions?|terima\s+kasih|lah|la|je|sahaja|now)?$', msg):
            return True

        return False

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

    def _extract_origin_and_destination_candidates(
        self, message: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts raw (origin, destination) strings from user phrasing including Manglish:
        e.g. 'what good jalan to follow when I from vr lab to kernal', 'jalan dari A ke B'
        """
        msg_clean = message.strip().rstrip("?.!,")

        patterns = [
            # 1. "from <origin> to <dest>" / "dari <origin> ke <dest>" (prefix-resilient)
            r'(?:.*?\b)?(?:from|dari|dr)\s+(.+?)\s+(?:to|ke|towards|sampai)\s+(.+)',
            # 2. "between <origin> and <dest>" / "antara <origin> dan <dest>"
            r'(?:.*?\b)?(?:between|antara)\s+(.+?)\s+(?:and|dan|with|dengan)\s+(.+)',
            # 3. "<dest> from <origin>"
            r'(?:.*?\b)?(?:to|ke|towards)\s+(.+?)\s+(?:from|dari|dr)\s+(.+)',
            # 4. Direct "<origin> to <dest>" without "from" prefix
            r'^(?:can\s+you\s+)?(?:show\s+(?:me\s+)?)?(?:short\s+|shortest\s+|nearest\s+)?(?:path\s+|route\s+|jalan\s+)?(?:from\s+)?(.+?)\s+(?:to|ke|towards)\s+(.+)$',
        ]

        for idx, pattern in enumerate(patterns):
            match = re.search(pattern, msg_clean, re.IGNORECASE)
            if match:
                g1, g2 = match.group(1).strip(), match.group(2).strip()

                # If pattern 4 (without explicit 'from' prefix), ensure g1 is not a navigation command or filler
                if idx == 3:
                    nav_command_pattern = r'\b(take\s+me|bring\s+me|guide\s+me|lead\s+me|direct\s+me|bawa\s+saya|bawa|hantar\s+saya|pandu\s+saya|go|pergi|nak\s+pergi|walk|jalan|ouhh|ohh|i\s+see)\b'
                    if re.search(nav_command_pattern, g1, re.I):
                        continue

                if idx == 2:
                    dest_cand, orig_cand = g1, g2
                else:
                    orig_cand, dest_cand = g1, g2

                # If query contains sequential multi-stop clauses ("but first", "before that"), let sequential handler process it
                if any(w in dest_cand.lower() for w in ["but first", "before that", "before this", "first then"]):
                    continue

                # Clean polite, navigational, or Manglish filler words
                clean_re = r'\b(please|pls|can you|can i|could you|show me|tell me|give me|take me|bring me|guide me|lead me|bawa saya|short|shortest|nearest|fastest|quickest|path|route|way|jalan|laluan|walk|how to get|how do i get|good|best|what|when i|bila saya|nak|nak pegi|nak pergi|instead|ouhh|ohh|i see)\b'
                orig_clean = re.sub(clean_re, '', orig_cand, flags=re.I).strip()
                dest_clean = re.sub(clean_re, '', dest_cand, flags=re.I).strip()

                # If orig_clean is empty after stripping filler commands, then no real origin was provided
                if not orig_clean:
                    continue

                # For Pattern 4 (no explicit 'from'), candidate origin MUST be a recognized campus location
                if idx == 3 and not self._find_location_in_text(orig_clean):
                    continue

                final_orig = orig_clean
                final_dest = dest_clean if dest_clean else dest_cand

                if final_orig and final_dest:
                    return final_orig, final_dest

        return None, None

    def _extract_origin_and_destination(
        self, message: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """
        Extracts both origin and destination objects and candidate strings.
        Returns: (orig_loc, dest_loc, orig_cand_str, dest_cand_str)
        """
        orig_cand, dest_cand = self._extract_origin_and_destination_candidates(message)
        if not orig_cand or not dest_cand:
            return None, None, None, None

        orig_loc = self._find_location_in_text(orig_cand)
        dest_loc = self._find_location_in_text(dest_cand)

        return orig_loc, dest_loc, orig_cand, dest_cand

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

    def _check_non_existent_facility(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Detects requests for facilities or room numbers that do not exist in FTMK:
        - Non-existent numbered labs (AI Lab 5+, BK 8-12, SE Lab 4+, etc.)
        - Amenities outside FTMK (ATM, bank, gym, swimming pool, dorm, lift, etc.)
        """
        msg_lower = message.lower().strip()

        # 1. AI Labs (FTMK only has AI Labs 1, 2, 3, 4 in Block B, Level 2)
        ai_match = re.search(r'\b(?:makmal\s+)?(?:ai|artificial\s+intelligence)\s*(?:lab(?:oratory)?)?\s*([0-9]+)\b', msg_lower)
        if ai_match:
            num = int(ai_match.group(1))
            if num < 1 or num > 4:
                return {
                    "reply": (
                        f"❌ **AI Lab {num} does not exist in FTMK.**\n\n"
                        f"FTMK only has **4 AI Labs**:\n"
                        f"• **AI Lab 1 & AI Lab 2** (Block B, Level 2)\n"
                        f"• **AI Lab 3 & AI Lab 4 (FAIX)** (Block B, Level 2)\n\n"
                        f"Would you like directions to one of these AI labs?"
                    ),
                    "intent": "LOCATION_QUERY",
                    "destination_id": None,
                }

        # 2. Programming Labs (FTMK only has Prog Labs 1-4)
        prog_match = re.search(r'\b(?:makmal\s+)?(?:prog(?:ram(?:ming)?)?|pengaturcaraan)\s*(?:lab(?:oratory)?)?\s*([0-9]+)\b', msg_lower)
        if prog_match:
            num = int(prog_match.group(1))
            if num < 1 or num > 4:
                return {
                    "reply": (
                        f"❌ **Programming Lab {num} does not exist in FTMK.**\n\n"
                        f"FTMK only has **Programming Labs 1, 2, 3, and 4**:\n"
                        f"• **Programming Lab 1 & 2:** Block B, Level 1\n"
                        f"• **Programming Lab 3 & 4:** Block C, Level 4\n\n"
                        f"Which programming lab would you like to visit?"
                    ),
                    "intent": "LOCATION_QUERY",
                    "destination_id": None,
                }

        # 3. Software Engineering Labs (FTMK only has SE Labs 1-3 in Block C, Level 1)
        se_match = re.search(r'\b(?:makmal\s+)?(?:soft(?:ware)?\s*eng(?:ineering)?|se|kejuruteraan\s+perisian)\s*(?:lab(?:oratory)?)?\s*([0-9]+)\b', msg_lower)
        if se_match:
            num = int(se_match.group(1))
            if num < 1 or num > 3:
                return {
                    "reply": (
                        f"❌ **Software Engineering Lab {num} does not exist in FTMK.**\n\n"
                        f"FTMK only has **Software Engineering Labs 1, 2, and 3** (all located in **Block C, Level 1**).\n\n"
                        f"Would you like directions to one of them?"
                    ),
                    "intent": "LOCATION_QUERY",
                    "destination_id": None,
                }

        # 4. Database Labs (FTMK only has DB Labs 1-3 in Block C, Level 2)
        db_match = re.search(r'\b(?:makmal\s+)?(?:data(?:base)?|db|pangkalan\s+data)\s*(?:lab(?:oratory)?)?\s*([0-9]+)\b', msg_lower)
        if db_match:
            num = int(db_match.group(1))
            if num < 1 or num > 3:
                return {
                    "reply": (
                        f"❌ **Database Lab {num} does not exist in FTMK.**\n\n"
                        f"FTMK only has **Database Labs 1, 2, and 3** (all located in **Block C, Level 2**).\n\n"
                        f"Which database lab are you looking for?"
                    ),
                    "intent": "LOCATION_QUERY",
                    "destination_id": None,
                }

        # 5. Multimedia Labs (FTMK only has MM Labs 1-4 in Block D)
        mm_match = re.search(r'\b(?:makmal\s+)?(?:multi(?:media)?|mm)\s*(?:lab(?:oratory)?)?\s*([0-9]+)\b', msg_lower)
        if mm_match:
            num = int(mm_match.group(1))
            if num < 1 or num > 4:
                return {
                    "reply": (
                        f"❌ **Multimedia Lab {num} does not exist in FTMK.**\n\n"
                        f"FTMK has **Multimedia Labs 1, 2, 3, and 4**:\n"
                        f"• **Multimedia Lab 1 & 2:** Block D, Level 2\n"
                        f"• **Multimedia Lab 3 & 4:** Block D, Level 3\n\n"
                        f"Which multimedia lab do you need?"
                    ),
                    "intent": "LOCATION_QUERY",
                    "destination_id": None,
                }

        # 6. Network Labs (FTMK only has Network Labs 1 & 2)
        net_match = re.search(r'\b(?:makmal\s+)?(?:net(?:work)?|rangkaian)\s*(?:lab(?:oratory)?)?\s*([0-9]+)\b', msg_lower)
        if net_match:
            num = int(net_match.group(1))
            if num < 1 or num > 2:
                return {
                    "reply": (
                        f"❌ **Network Lab {num} does not exist in FTMK.**\n\n"
                        f"FTMK only has **Network Labs 1 and 2**:\n"
                        f"• **Network Lab 1:** Block C, Level 3\n"
                        f"• **Network Lab 2:** Block C, Level 2\n\n"
                        f"Would you like directions to either of them?"
                    ),
                    "intent": "LOCATION_QUERY",
                    "destination_id": None,
                }

        # 7. Lecture Rooms (BK 1-7, 13, 14, 15, 16 exist; 8-12 and 17+ DO NOT)
        bk_match = re.search(r'\b(?:bilik\s*kuliah|lec(?:ture)?\s*room|bk)\s*([0-9]+)\b', msg_lower)
        if bk_match:
            num = int(bk_match.group(1))
            valid_bks = {1, 2, 3, 4, 5, 6, 7, 13, 14, 15, 16}
            if num not in valid_bks:
                return {
                    "reply": (
                        f"❌ **Lecture Room {num} (BK {num}) does not exist in FTMK.**\n\n"
                        f"Available Lecture Rooms in FTMK are:\n"
                        f"• **Block C (Level 1):** BK 1, BK 2, BK 3, BK 4, BK 5\n"
                        f"• **Block B (Level 1):** BK 6, BK 7\n"
                        f"• **Block E (Level 1):** BK 13\n"
                        f"• **Block D (Level 1):** BK 14\n"
                        f"• **Block B (Level 3 & 4):** BK 15, BK 16\n\n"
                        f"Which lecture room are you looking for?"
                    ),
                    "intent": "LOCATION_QUERY",
                    "destination_id": None,
                }

        # 8. Non-campus amenities
        if re.search(r'\b(atm|bank|cash machine|mesin atm)\b', msg_lower):
            return {
                "reply": (
                    "🏧 **ATMs are not located inside the FTMK building.**\n\n"
                    "The nearest ATMs (CIMB and Bank Islam) are located at the **Student Affairs Building (HEPA) / Central Campus**.\n\n"
                    "Is there a faculty facility or classroom you need help finding inside FTMK?"
                ),
                "intent": "FACILITY_INFO",
                "destination_id": None,
            }

        if re.search(r'\b(gym|gymnasium|swimming pool|kolam renang|stadium)\b', msg_lower):
            return {
                "reply": (
                    "🏃 **Sports and gym facilities are not located in FTMK.**\n\n"
                    "The university Gymnasium, Sports Complex, and swimming pool are located at the **Central UTeM Campus**.\n\n"
                    "Let me know if you need any directions within FTMK!"
                ),
                "intent": "FACILITY_INFO",
                "destination_id": None,
            }

        if re.search(r'\b(lift|elevator|escalator|eskalator)\b', msg_lower):
            return {
                "reply": (
                    "ℹ️ **FTMK does not have elevators (lifts) or escalators for general access.**\n\n"
                    "Movement between levels is via the central stairs located in each block (Blocks A, B, C, D, and E) "
                    "as well as connecting walkways and bridges on Levels 1, 2, 3, and 4."
                ),
                "intent": "FACILITY_INFO",
                "destination_id": None,
            }

        if re.search(r'\b(surau|prayer room|musolla|solat)\b', msg_lower):
            return {
                "reply": (
                    "🕌 **Surau / Prayer Rooms at FTMK:**\n\n"
                    "Dedicated prayer rooms for Muslim students and staff are located at:\n"
                    "• **Block A, Level 1 Surau** (near Main Entrance)\n"
                    "• **Block D, Level 1 Surau**\n\n"
                    "Both provide ablution areas for male and female prayer. Would you like directions to the Block A Surau?"
                ),
                "intent": "FACILITY_INFO",
                "destination_id": "MAIN_ENTRANCE",
            }

    def _handle_sequential_destinations(
        self, message: str, session_mem: Dict[str, Any], current_loc: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handles multi-stop sequential requests:
        e.g. 'bring me to ai lab 4 but first I need to go to program lab first'
        e.g. 'first go to program lab then ai lab 4'
        """
        msg_clean = message.strip().rstrip("?.!,")

        # Pattern 1: "<dest_final> but first (go to) <dest_first> (first)"
        p1 = r'(?:bring\s+me\s+to|take\s+me\s+to|guide\s+me\s+to|lead\s+me\s+to|go\s+to|navigate\s+to)?\s*(.+?)\s+(?:but\s+first|before\s+that|before\s+this)\s+(?:i\s+need\s+to\s+go\s+to\s+|i\s+want\s+to\s+go\s+to\s+|go\s+to\s+|nak\s+pergi\s+ke\s+)?(.+?)(?:\s+first)?$'
        # Pattern 2: "first (go to) <dest_first> (and) then (go to) <dest_final>"
        p2 = r'^(?:first\s+(?:go\s+to\s+|i\s+need\s+to\s+go\s+to\s+|i\s+want\s+to\s+go\s+to\s+)?)(.+?)\s+(?:then|after\s+that|and\s+then)\s+(?:go\s+to\s+|proceed\s+to\s+)?(.+)$'
        # Pattern 3: "<dest_first> first (and) then <dest_final>"
        p3 = r'^(.+?)\s+first\s+(?:then|after\s+that|and\s+then)\s+(?:go\s+to\s+|proceed\s+to\s+)?(.+)$'

        match1 = re.search(p1, msg_clean, re.I)
        match2 = re.search(p2, msg_clean, re.I)
        match3 = re.search(p3, msg_clean, re.I)

        cand_first = None
        cand_final = None

        if match1:
            cand_final = match1.group(1).strip()
            cand_first = match1.group(2).strip()
        elif match2:
            cand_first = match2.group(1).strip()
            cand_final = match2.group(2).strip()
        elif match3:
            cand_first = match3.group(1).strip()
            cand_final = match3.group(2).strip()

        if not cand_first or not cand_final:
            return None

        # Clean filler words
        clean_filler = r'\b(please|pls|can you|bring me|take me|guide me|go to|i need to go to|i want to|nak pergi ke|first|then)\b'
        cand_first = re.sub(clean_filler, '', cand_first, flags=re.I).strip()
        cand_final = re.sub(clean_filler, '', cand_final, flags=re.I).strip()

        loc_first = self._find_location_in_text(cand_first)
        loc_final = self._find_location_in_text(cand_final)

        if not loc_first and not loc_final:
            return None

        # Case: Both locations are recognized
        if loc_first and loc_final:
            name1 = loc_first["name"]
            bld1 = loc_first.get("building", "FTMK")
            flr1 = loc_first.get("floor", 1)
            id1 = loc_first["id"]

            name2 = loc_final["name"]
            bld2 = loc_final.get("building", "FTMK")
            flr2 = loc_final.get("floor", 1)
            id2 = loc_final["id"]

            # Route Leg 1: current_loc -> loc_first
            leg1_calc = self.routing_service.get_shortest_route(current_loc, id1)
            dist1 = leg1_calc.get("total_distance", 0) if "status" in leg1_calc and leg1_calc["status"] == "success" else 0
            steps1 = "\n".join(f"{i+1}. {step}" for i, step in enumerate(leg1_calc.get("instructions", []))) if leg1_calc else ""

            # Route Leg 2: loc_first -> loc_final
            leg2_calc = self.routing_service.get_shortest_route(id1, id2)
            dist2 = leg2_calc.get("total_distance", 0) if "status" in leg2_calc and leg2_calc["status"] == "success" else 0

            if bld1 == bld2 and flr1 == flr2:
                leg2_note = f"Both rooms are on the same floor in **{bld1}, Level {flr1}** (~{dist2}m apart). Walk along the corridor to reach {name2}."
            elif bld1 == bld2:
                leg2_note = f"Both rooms are in **{bld1}**! Take the stairs between Level {flr1} and Level {flr2} (~{dist2}m walk) to reach {name2}."
            else:
                leg2_note = f"From {name1} ({bld1}), follow the covered walkways connecting to {bld2}, Level {flr2} (~{dist2}m walk)."

            reply = (
                f"🚶‍♂️ **Multi-Stop Route: {name1} ➔ {name2}:**\n\n"
                f"📍 **Stop 1:** {name1} ({bld1}, Level {flr1})\n"
                f"📍 **Stop 2:** {name2} ({bld2}, Level {flr2})\n\n"
                f"**Step 1: Walking to Stop 1 ({name1}) from {current_loc} ({dist1}m):**\n"
                f"{steps1}\n\n"
                f"**Step 2: Connecting to Stop 2 ({name2}):**\n"
                f"• {leg2_note}\n\n"
                f"Would you like walking directions starting directly from {name1} to {name2}?"
            )

            session_mem["last_destination"] = loc_final
            session_mem["direction_destination"] = loc_final
            session_mem["direction_origin"] = loc_first
            session_mem["last_building"] = bld2
            session_mem["awaiting_direction_confirmation"] = True

            return {
                "reply": reply,
                "intent": "GUIDANCE_REQUEST",
                "destination_id": id1,
                "confidence": 1.0,
                "entities": {
                    "destination": name1,
                    "category": loc_first.get("category"),
                    "building": bld1,
                },
                "handoff": {
                    "type": "NAVIGATION",
                    "start_id": current_loc,
                    "destination_id": id1,
                    "destination_name": name1,
                    "route": leg1_calc,
                },
                "route_info": leg1_calc,
                "recommendations": None,
                "error": None,
            }

        return None

    def _handle_faculty_overview(self, message: str) -> Optional[str]:
        """
        Handles general faculty / campus overview queries:
        e.g. 'what have in ftmk', 'in ftmk what facilitity haver', 'can you give information about ftmk',
        'what is in ftmk', 'apa ada kat ftmk', 'what does ftmk have', etc.
        """
        preprocessed = CampusNLP.preprocess_text(message) if CampusNLP else message.lower().strip()
        msg_clean = re.sub(r'[^\w\s]', '', preprocessed).strip()

        overview_patterns = [
            r'\bwhat\s+(?:do\s+you\s+)?have\s+in\s+(?:the\s+)?(?:ftmk|faculty|fakulti|campus)\b',
            r'\bin\s+(?:the\s+)?(?:ftmk|faculty|fakulti)\s+what\s+(?:facility|facilities)\s+have\b',
            r'\bin\s+(?:the\s+)?(?:ftmk|faculty|fakulti)\s+what\s+have\b',
            r'\bwhat\s+(?:facility|facilities)\s+(?:do\s+you\s+have|are\s+there|have)\s+in\s+(?:the\s+)?(?:ftmk|faculty|fakulti)\b',
            r'\bwhat\s+is\s+in\s+(?:the\s+)?(?:ftmk|faculty|fakulti)\b',
            r'\bwhat\s+are\s+in\s+(?:the\s+)?(?:ftmk|faculty|fakulti)\b',
            r'\bwhat\s+does\s+(?:ftmk|the\s+faculty)\s+have\b',
            r'\bwhats\s+in\s+(?:ftmk|the\s+faculty)\b',
            r'\binformation\s+about\s+(?:ftmk|the\s+faculty)\b',
            r'\binfo\s+about\s+(?:ftmk|the\s+faculty)\b',
            r'\btell\s+me\s+about\s+(?:ftmk|the\s+faculty)\b',
            r'\babout\s+ftmk\b',
            r'\bfaculty\s+overview\b',
            r'\bftmk\s+overview\b',
            r'\bapa\s+ada\s+(?:kat|dekat|di|dalam)\s+(?:ftmk|fakulti)\b',
            r'\bapa\s+kemudahan\s+(?:kat|dekat|di|dalam)\s+(?:ftmk|fakulti)\b',
            r'\bsenarai\s+kemudahan\s+(?:ftmk|fakulti)\b',
            r'\bfacilities\s+in\s+(?:the\s+)?(?:ftmk|faculty)\b',
        ]

        is_match = any(re.search(p, msg_clean, re.I) for p in overview_patterns) or msg_clean in {
            "what have in ftmk", "what have in faculty", "in ftmk what facility have",
            "information about ftmk", "give information about ftmk", "info about ftmk",
            "tell me about ftmk", "about ftmk", "apa ada kat ftmk", "apa ada di ftmk",
            "apa ada dalam ftmk", "apa kemudahan di ftmk", "facilities in ftmk"
        }

        if is_match:
            return (
                "🏛️ **Overview of FTMK (Faculty of Information & Communication Technology):**\n\n"
                "FTMK is organized across **5 interconnected blocks (Blocks A to E)** spanning **Levels 1 to 4**:\n\n"
                "• **🏢 Block A (Administration & Main Entrance):**\n"
                "  - **Level 1:** Main Entrance / Lobby, C-ACT, Local Food Vendors (Nasi Lemak, Kuih & Drinks), Surau\n"
                "  - **Level 2 & 3:** Discussion Rooms, Academic & Administrative Offices, Skybridge to Block B\n"
                "  - **Level 4:** Seminar Hall & Main Meeting Room\n\n"
                "• **💻 Block B (AI, Programming & Workshops):**\n"
                "  - **Level 1:** Programming Labs 1 & 2, Bilik Kuliah 6 & 7, Bilik VIVA\n"
                "  - **Level 2:** AI Labs 1, 2, 3 & 4 (FAIX), Skybridge to Block A\n"
                "  - **Level 3 & 4:** Robotics Lab, BITI Workshop, Bilik Kuliah 15 & 16\n\n"
                "• **🖥️ Block C (Software, Databases & Networks):**\n"
                "  - **Level 1:** Software Engineering Labs 1–3, Bilik Kuliah 1–5\n"
                "  - **Level 2:** Database Labs 1–3, Network Lab 2\n"
                "  - **Level 3:** Systems and Hardware Lab, Network Lab 1\n"
                "  - **Level 4:** Programming Labs 3 & 4\n\n"
                "• **🎮 Block D (Multimedia, Metaverse & Creative Tech):**\n"
                "  - **Level 1:** Students' Common Room, Metaverse Studio, Bilik Kuliah 14, Surau\n"
                "  - **Level 2 & 3:** Multimedia Labs 1–4, VR Lab, Mini Theatre, Audio Recording Studios\n\n"
                "• **🛡️ Block E (Cybersecurity, CCNA & E-Sports):**\n"
                "  - **Level 1:** Game Arena, Bilik Kuliah 13\n"
                "  - **Level 2 & 3:** Cybersecurity Competence Center, CCNA & Fiber Optic Labs, Wireless & Cloud Computing Labs\n\n"
                "Would you like walking directions or more details about any of these rooms or facilities?"
            )

        return None

    def _handle_proximity_comparison(
        self, message: str, session_mem: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handles pairwise proximity inquiries between two locations:
        e.g. 'kernel room near with bk1?', 'is ai lab 1 near bk1?', 'adakah bilik seminar dekat bilik viva', etc.
        Detects if either location is non-existent in FTMK and explains clearly.
        """
        preprocessed = CampusNLP.preprocess_text(message) if CampusNLP else message.strip()
        msg_clean = preprocessed.rstrip("?.!,")

        # Patterns matching pairwise comparison:
        # 1. "(is) <A> near/close to/beside (with/to) <B>"
        # 2. "(are) <A> and <B> near/close/beside"
        # 3. "<A> dekat / berdekatan / sebelah (dengan) <B>"
        prox_pattern1 = r'^(?:is\s+|adakah\s+)?(.+?)\s+(?:is\s+)?(?:near|nearby|close\s+to|close|beside|next\s+to|adjacent\s+to|sebelah|dekat(?:\s+dengan)?|berdekatan(?:\s+dengan)?)\s+(?:with\s+|to\s+|and\s+|dan\s+|dgn\s+)?(.+)$'
        prox_pattern2 = r'^(?:are\s+|adakah\s+)?(.+?)\s+(?:and|dan|with|dengan)\s+(.+?)\s+(?:near|close|close\s+to|beside|next\s+to|adjacent|sebelah|dekat|berdekatan)$'

        match = re.search(prox_pattern1, msg_clean, re.I)
        if not match:
            match = re.search(prox_pattern2, msg_clean, re.I)

        if not match:
            return None

        cand_a = match.group(1).strip()
        cand_b = match.group(2).strip()

        # Filter out question words if accidentally captured
        strip_words = r'^(?:is\s+there\s+any|is\s+|there\s+|any\s+|the\s+)'
        cand_a = re.sub(strip_words, '', cand_a, flags=re.I).strip()
        strip_end = r'\s+(?:ke|kah)$'
        cand_b = re.sub(strip_end, '', cand_b, flags=re.I).strip()

        # If cand_a is a question word like "what" or "what is", this is a general surrounding query, not pairwise!
        if cand_a.lower() in {"what", "what is", "whats", "what are", "which", "apa", "apa ada", "ada apa", "which room", "which facility"}:
            return None

        loc_a = self._find_location_in_text(cand_a)
        loc_b = self._find_location_in_text(cand_b)

        # Case 1: Both locations DO NOT exist in FTMK
        if not loc_a and not loc_b:
            reply = (
                f"❌ Neither **'{cand_a.title()}'** nor **'{cand_b.title()}'** were recognized as facilities in FTMK.\n\n"
                f"FTMK consists of 5 academic blocks (Blocks A to E) across Levels 1 to 4. "
                f"Could you verify the room names you are searching for?"
            )
            return {
                "reply": reply,
                "intent": "LOCATION_QUERY",
                "destination_id": None,
                "confidence": 1.0,
                "entities": {"destination": None, "category": None, "building": None},
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "error": None,
            }

        # Case 2: Cand A does NOT exist, but Loc B DOES exist (Exact match for 'kernel room near with bk1?')
        if not loc_a and loc_b:
            b_name = loc_b["name"]
            b_bld = loc_b.get("building", "FTMK")
            b_flr = loc_b.get("floor", 1)

            # Get neighbors of B
            neighbors = [
                l["name"] for l in self.repository.filter_by_building(b_bld)
                if l.get("floor") == b_flr and l["id"] != loc_b["id"]
            ]
            neighbor_snippet = ""
            if neighbors:
                neighbor_snippet = f"\nAlong the same corridor in {b_bld}, Level {b_flr}, you will find:\n" + "\n".join(f"• **{n}**" for n in neighbors[:4])

            reply = (
                f"❌ **'{cand_a.title()}' does not exist in FTMK.**\n\n"
                f"**{b_name}** is located in **{b_bld}, Level {b_flr}**.{neighbor_snippet}\n\n"
                f"Would you like walking directions to {b_name}?"
            )
            session_mem["last_destination"] = loc_b
            session_mem["direction_destination"] = loc_b
            session_mem["last_building"] = b_bld
            session_mem["awaiting_direction_confirmation"] = True

            return {
                "reply": reply,
                "intent": "LOCATION_QUERY",
                "destination_id": loc_b["id"],
                "confidence": 1.0,
                "entities": {
                    "destination": b_name,
                    "category": loc_b.get("category"),
                    "building": b_bld,
                },
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "error": None,
            }

        # Case 3: Loc A DOES exist, but Cand B does NOT exist
        if loc_a and not loc_b:
            a_name = loc_a["name"]
            a_bld = loc_a.get("building", "FTMK")
            a_flr = loc_a.get("floor", 1)

            neighbors = [
                l["name"] for l in self.repository.filter_by_building(a_bld)
                if l.get("floor") == a_flr and l["id"] != loc_a["id"]
            ]
            neighbor_snippet = ""
            if neighbors:
                neighbor_snippet = f"\nAlong the same corridor in {a_bld}, Level {a_flr}, you will find:\n" + "\n".join(f"• **{n}**" for n in neighbors[:4])

            reply = (
                f"❌ **'{cand_b.title()}' does not exist in FTMK.**\n\n"
                f"**{a_name}** is located in **{a_bld}, Level {a_flr}**.{neighbor_snippet}\n\n"
                f"Would you like walking directions to {a_name}?"
            )
            session_mem["last_destination"] = loc_a
            session_mem["direction_destination"] = loc_a
            session_mem["last_building"] = a_bld
            session_mem["awaiting_direction_confirmation"] = True

            return {
                "reply": reply,
                "intent": "LOCATION_QUERY",
                "destination_id": loc_a["id"],
                "confidence": 1.0,
                "entities": {
                    "destination": a_name,
                    "category": loc_a.get("category"),
                    "building": a_bld,
                },
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "error": None,
            }

        # Case 4: BOTH locations exist in FTMK!
        a_id = loc_a["id"]
        b_id = loc_b["id"]
        a_name = loc_a["name"]
        b_name = loc_b["name"]
        a_bld = loc_a.get("building", "FTMK")
        a_flr = loc_a.get("floor", 1)
        b_bld = loc_b.get("building", "FTMK")
        b_flr = loc_b.get("floor", 1)

        route_calc = self.routing_service.get_shortest_route(a_id, b_id)
        dist = route_calc.get("total_distance", 0) if "status" in route_calc and route_calc["status"] == "success" else 0

        if a_id == b_id:
            reply = f"📍 **{a_name}** and **{b_name}** refer to the same location!"
        elif a_bld == b_bld and a_flr == b_flr:
            reply = (
                f"✅ **Yes, {a_name} and {b_name} are very close to each other!**\n\n"
                f"Both are situated along the same corridor in **{a_bld}, Level {a_flr}** "
                f"(approximately **{dist}m** apart).\n\n"
                f"Would you like walking directions between them?"
            )
        elif a_bld == b_bld and a_flr != b_flr:
            reply = (
                f"📍 **{a_name} and {b_name} are in the same block ({a_bld}), but on different levels:**\n"
                f"• **{a_name}:** Level {a_flr}\n"
                f"• **{b_name}:** Level {b_flr}\n\n"
                f"Walking distance between them is approximately **{dist}m** (accessible via the central stairs of {a_bld}).\n\n"
                f"Would you like walking directions between them?"
            )
        else:
            reply = (
                f"📍 **No, they are located in different blocks:**\n"
                f"• **{a_name}:** {a_bld}, Level {a_flr}\n"
                f"• **{b_name}:** {b_bld}, Level {b_flr}\n\n"
                f"Walking distance between them is approximately **{dist}m**.\n\n"
                f"Would you like walking directions between them?"
            )

        session_mem["last_destination"] = loc_b
        session_mem["direction_destination"] = loc_b
        session_mem["direction_origin"] = loc_a
        session_mem["awaiting_direction_confirmation"] = True

        return {
            "reply": reply,
            "intent": "FACILITY_INFO",
            "destination_id": b_id,
            "confidence": 1.0,
            "entities": {
                "destination": b_name,
                "category": loc_b.get("category"),
                "building": b_bld,
            },
            "handoff": None,
            "route_info": None,
            "recommendations": None,
            "error": None,
        }

    def _handle_surrounding_query(
        self, message: str, session_mem: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handles queries asking what is around, near, beside, or surrounding a location:
        e.g. 'what surrond ai 1', 'what is near AI Lab 1', 'apa ada dekat bilik viva', etc.
        """
        msg_lower = message.lower().strip()
        surround_kws = [
            "surround", "surrounds", "surrounding", "surrond", "suround",
            "around", "near", "nearby", "beside", "next to", "adjacent", "close to",
            "sebelah", "dekat", "berdekatan", "sekitar", "keliling", "apa ada dekat", "ada apa dekat"
        ]

        if not any(kw in msg_lower for kw in surround_kws):
            return None

        # Clean filler surrounding words to isolate the location name
        cleaned_text = re.sub(
            r'\b(what|what is|whats|what are|which|facilities|rooms?|labs?|surround|surrounds|surrounding|surrond|suround|around|near|nearby|beside|next to|adjacent|close to|sebelah|dekat|berdekatan|sekitar|keliling|apa ada|ada apa|show me|tell me|is there|ada)\b',
            '',
            msg_lower,
            flags=re.I
        ).strip()

        target_loc = (
            self._find_location_in_text(cleaned_text)
            or self._find_location_in_text(message)
            or session_mem.get("last_destination")
        )

        if not target_loc:
            return None

        loc_id = target_loc["id"]
        loc_name = target_loc["name"]
        bld = target_loc.get("building", "Block B")
        flr = target_loc.get("floor", 2)

        # Find all other facilities in the same building on the same floor
        same_floor_locs = [
            loc for loc in self.repository.filter_by_building(bld)
            if loc.get("floor") == flr and loc["id"] != loc_id
        ]

        # Check for connecting bridges on this floor
        bridge_info = ""
        if bld == "Block A" and flr == 2:
            bridge_info = "• **Bridge to Block B:** Direct elevated walkway connecting to Block B (Level 2)\n"
        elif bld == "Block B" and flr == 2:
            bridge_info = "• **Bridge to Block A:** Direct elevated walkway connecting to Block A (Level 2)\n"

        if same_floor_locs or bridge_info:
            places_list = "\n".join(f"• **{l['name']}**" for l in same_floor_locs)
            reply = (
                f"🏢 **Facilities surrounding {loc_name} ({bld}, Level {flr}):**\n\n"
                f"Along this corridor and on this same floor, you will find:\n"
                f"{places_list}\n"
                f"{bridge_info}\n"
                f"Would you like walking directions to any of these neighboring rooms?"
            )
        else:
            reply = (
                f"📍 **{loc_name}** is situated in **{bld}, Level {flr}**.\n\n"
                f"Would you like walking directions to this room?"
            )

        session_mem["last_options_list"] = same_floor_locs
        session_mem["last_destination"] = target_loc
        session_mem["last_building"] = bld
        session_mem["direction_destination"] = target_loc
        session_mem["awaiting_direction_confirmation"] = True

        return {
            "reply": reply,
            "intent": "FACILITY_INFO",
            "destination_id": loc_id,
            "confidence": 1.0,
            "entities": {
                "destination": loc_name,
                "category": target_loc.get("category"),
                "building": bld,
            },
            "handoff": None,
            "route_info": None,
            "recommendations": None,
            "error": None,
        }

    def _handle_floor_level_query(
        self, message: str, session_mem: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handles queries asking what is on a specific level / floor:
        e.g. 'what is on level 2', 'what's in block b level 1', 'apa ada kat tingkat 3', 'level 1 rooms'
        """
        msg_lower = message.lower().strip()
        floor_match = re.search(r'\b(?:level|aras|tingkat|floor)\s*([1-4])\b', msg_lower)
        if not floor_match:
            return None

        # Check if user is asking for facilities on that level
        is_inquiry = any(w in msg_lower for w in ["what", "ada", "show", "list", "tell", "rooms", "labs", "facilities", "which"]) or len(msg_lower.split()) <= 4
        if not is_inquiry:
            return None

        floor_num = int(floor_match.group(1))
        block_match = re.search(r'\bblock\s+([a-e])\b', msg_lower)

        if block_match:
            block_letter = block_match.group(1).upper()
            block_name = f"Block {block_letter}"
            locs = [
                l for l in self.repository.filter_by_building(block_name)
                if l.get("floor") == floor_num
            ]
            if not locs:
                return None

            session_mem["last_options_list"] = locs
            places = "\n".join(f"• **{l['name']}**" for l in locs)
            reply = (
                f"🏢 **Facilities on Level {floor_num} of {block_name}:**\n\n"
                f"{places}\n\n"
                f"Would you like walking directions to any of these rooms?"
            )
            return {
                "reply": reply,
                "intent": "FACILITY_INFO",
                "destination_id": None,
                "confidence": 1.0,
                "entities": {"destination": None, "category": "floor_overview", "building": block_name},
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "error": None,
            }

        else:
            # Query across ALL blocks for this level
            all_locs = [l for l in self.repository.get_all() if l.get("floor") == floor_num]
            if not all_locs:
                return None

            session_mem["last_options_list"] = all_locs
            by_bld: Dict[str, List[str]] = {}
            for l in all_locs:
                bld = l.get("building", "FTMK")
                by_bld.setdefault(bld, []).append(l["name"])

            lines = [f"🏢 **Overview of Facilities on Level {floor_num} across FTMK:**\n"]
            for bld in sorted(by_bld.keys()):
                rooms_summary = " • ".join(by_bld[bld][:4])
                more = f" *(+{len(by_bld[bld])-4} more)*" if len(by_bld[bld]) > 4 else ""
                lines.append(f"• **{bld}:** {rooms_summary}{more}")

            lines.append("\nWhich room or block would you like directions to?")
            return {
                "reply": "\n".join(lines),
                "intent": "FACILITY_INFO",
                "destination_id": None,
                "confidence": 1.0,
                "entities": {"destination": None, "category": "floor_overview", "building": None},
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "error": None,
            }

    def _handle_distance_time_query(
        self, message: str, session_mem: Dict[str, Any], current_loc: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handles questions asking about distance, travel time, or effort:
        e.g. 'how far is it?', 'how long does it take?', 'is it far from here?', 'berapa minit nak sampai?', 'jauh tak?'
        """
        msg_lower = message.lower().strip()
        time_dist_patterns = [
            r'\bhow\s+far\b',
            r'\bhow\s+long\s+(?:to\s+walk|does\s+it\s+take|will\s+it\s+take)\b',
            r'\bhow\s+many\s+minutes\b',
            r'\bis\s+it\s+far\b',
            r'\bjauh\s+tak\b',
            r'\bjauh\s+ke\b',
            r'\bberapa\s+jauh\b',
            r'\bberapa\s+lama\b',
            r'\bberapa\s+minit\b',
            r'\bwalking\s+time\b',
            r'\bestimated\s+time\b',
        ]

        if not any(re.search(p, msg_lower) for p in time_dist_patterns):
            return None

        # Determine target destination: either mentioned in text or from context
        target_loc = self._find_location_in_text(message) or session_mem.get("direction_destination") or session_mem.get("last_destination")
        if not target_loc:
            return None

        target_id = target_loc["id"]
        target_name = target_loc["name"]
        bld = target_loc.get("building", "FTMK")
        flr = target_loc.get("floor", 1)

        route_calc = self.routing_service.get_shortest_route(current_loc, target_id)
        if "status" in route_calc and route_calc["status"] == "success":
            dist = route_calc.get("total_distance", 0)
            start_name = route_calc.get("start", current_loc)
            # Average walking speed ~ 65 meters per minute
            walking_mins = max(1, round(dist / 65)) if dist > 30 else 1

            if dist == 0:
                time_str = "You are already right outside this location!"
            elif dist <= 30:
                time_str = f"It's just **{dist}m** away — less than a 1-minute easy walk! You are practically right there."
            elif dist <= 75:
                time_str = f"It's approximately **{dist}m** away, which is about a **1 to 2 minute** easy walk."
            else:
                time_str = f"It is about **{dist}m** away, taking approximately **{walking_mins} minutes** of walking."

            reply = (
                f"⏱️ **Distance & Estimated Walking Time to {target_name}:**\n\n"
                f"• **Location:** {bld}, Level {flr}\n"
                f"• **From:** {start_name}\n"
                f"• **Estimate:** {time_str}\n\n"
                f"Would you like step-by-step walking directions there right now?"
            )

            session_mem["last_destination"] = target_loc
            session_mem["direction_destination"] = target_loc
            session_mem["awaiting_direction_confirmation"] = True

            return {
                "reply": reply,
                "intent": "FACILITY_INFO",
                "destination_id": target_id,
                "confidence": 1.0,
                "entities": {
                    "destination": target_name,
                    "category": target_loc.get("category"),
                    "building": bld,
                },
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "error": None,
            }

        return None

    def _handle_ordinal_selection(
        self, message: str, session_mem: Dict[str, Any], current_loc: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handles user selecting an item from a previously presented list:
        e.g. 'take me to the first one', 'first room', 'the second one', 'number 1', 'no 2', 'yang pertama'
        """
        options = session_mem.get("last_options_list")
        if not options:
            return None

        msg_lower = message.lower().strip()
        ordinal_patterns = [
            (r'\b(?:the\s+)?(?:first|1st|number\s*1|no\s*1|nombor\s*1|pertama)\b', 0),
            (r'\b(?:the\s+)?(?:second|2nd|number\s*2|no\s*2|nombor\s*2|kedua)\b', 1),
            (r'\b(?:the\s+)?(?:third|3rd|number\s*3|no\s*3|nombor\s*3|ketiga)\b', 2),
            (r'\b(?:the\s+)?(?:fourth|4th|number\s*4|no\s*4|nombor\s*4|keempat)\b', 3),
            (r'\b(?:the\s+)?(?:fifth|5th|number\s*5|no\s*5|nombor\s*5|kelima)\b', 4),
        ]

        target_idx = None
        for pattern, idx in ordinal_patterns:
            if re.search(pattern, msg_lower):
                target_idx = idx
                break

        if target_idx is not None and target_idx < len(options):
            chosen = options[target_idx]
            session_mem["last_destination"] = chosen
            session_mem["direction_destination"] = chosen
            session_mem["last_building"] = chosen.get("building")
            session_mem["last_topic"] = chosen.get("category")
            session_mem["awaiting_direction_confirmation"] = False

            return self._build_walking_directions_response(current_loc, chosen)

        return None

    def _handle_conversational_questions(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Handles natural conversational small-talk and common campus queries:
        - Greetings / introductions
        - Gratitude & farewells
        - Campus amenities: WiFi, printing, parking
        - Academic / administrative offices, Dean's office
        - Study & group work spaces
        - Bridges & inter-block walkways
        - Lost student triage
        - Bot personality & vending machines
        """
        msg_lower = message.lower().strip()
        msg_clean = re.sub(r'[^\w\s]', '', msg_lower).strip()

        # 1. Greetings (fast-path)
        greetings = {"hi", "hai", "hello", "hey", "helo", "assalamualaikum", "salam", "selamat pagi", "selamat petang", "selamat tengahari", "good morning", "good afternoon", "good evening"}
        if msg_clean in greetings or any(msg_clean.startswith(g + " ") for g in greetings):
            if len(msg_clean.split()) <= 3:
                return {
                    "reply": "Hello! Welcome to FTMK. I am your AI campus concierge. How can I assist you with rooms, labs, or directions today? 😊",
                    "intent": "GREETING",
                    "destination_id": None,
                }

        # 2. Thank you / Gratitude
        thanks = {"thanks", "thank you", "terima kasih", "tq", "thx", "syukran", "much appreciated"}
        if msg_clean in thanks or any(t in msg_clean for t in thanks):
            return {
                "reply": "You're very welcome! 😊 Feel free to ask whenever you need help finding rooms or navigating around FTMK. Have a great day!",
                "intent": "GENERAL_HELP",
                "destination_id": None,
            }

        # 3. Goodbye / Farewell
        farewells = {"bye", "goodbye", "bye bye", "selamat tinggal", "jumpai lagi", "see you"}
        if msg_clean in farewells or any(f == msg_clean for f in farewells):
            return {
                "reply": "Goodbye! Take care and have a wonderful day at FTMK! 👋",
                "intent": "GENERAL_HELP",
                "destination_id": None,
            }

        # 4. Bot identity / capabilities
        if any(p in msg_lower for p in ["who are you", "what can you do", "siapa awak", "kamu siapa", "fungsi kamu", "what are you"]):
            return {
                "reply": (
                    "👋 **Hello! I am your FTMK AI Guidance Concierge.**\n\n"
                    "I can help you with:\n"
                    "• 🚶 **Walking Directions:** Step-by-step route guidance with distances between any two points\n"
                    "• 🏢 **Room & Lab Information:** Finding where any classroom, lab, or office is across Blocks A–E\n"
                    "• 🔍 **Surrounding Rooms:** Showing what facilities are on each floor or near a specific room\n"
                    "• ⏰ **Facility Details:** Operating hours, room capacities, and equipment\n"
                    "• 🍴 **Food & Amenities:** Directing you to food vendors at the lobby or restrooms on any floor\n\n"
                    "What would you like to explore?"
                ),
                "intent": "GENERAL_HELP",
                "destination_id": None,
            }

        # 5. WiFi
        if any(p in msg_lower for p in ["wifi", "wi-fi", "internet", "password wifi"]):
            return {
                "reply": (
                    "📶 **Campus Wi-Fi at FTMK:**\n\n"
                    "All blocks (A, B, C, D, E) are covered by university Wi-Fi:\n"
                    "• **eduroam:** Recommended for students and staff (log in with your UTeM email credentials).\n"
                    "• **UTeM-Guest:** For visitors (requires web portal registration).\n\n"
                    "Let me know if you need directions to any lab or study area!"
                ),
                "intent": "FACILITY_INFO",
                "destination_id": None,
            }

        # 6. Printing & Photostat
        if any(p in msg_lower for p in ["print", "printing", "photostat", "fotostat", "cetak"]):
            return {
                "reply": (
                    "🖨️ **Printing & Photostat Services:**\n\n"
                    "Printing facilities for students are available at:\n"
                    "• **C-ACT (Creative & Activity Room):** Block A, Level 1\n"
                    "• **Campus Convenience Shop:** Central Student Center\n\n"
                    "Would you like walking directions to C-ACT in Block A?"
                ),
                "intent": "FACILITY_INFO",
                "destination_id": "B_A_L1_C_ACT",
            }

        # 7. Parking
        if any(p in msg_lower for p in ["parking", "tempat letak kereta", "parkir", "park"]):
            return {
                "reply": (
                    "🚗 **Parking Areas for FTMK:**\n\n"
                    "• **Student Parking:** Located in the open parking lots behind Block C and adjacent to Block E.\n"
                    "• **Staff & Visitor Parking:** Designated bays right in front of the **Main Entrance (Block A)**.\n"
                    "• **Motorcycle Parking:** Covered bays situated near the entrance of Block E and Block B."
                ),
                "intent": "FACILITY_INFO",
                "destination_id": "MAIN_ENTRANCE",
            }

        # 8. Administrative Offices / Dean / Lecturers
        if any(p in msg_lower for p in ["dean", "dekan", "pejabat dekan", "academic office", "pejabat akademik", "admin office", "pejabat pentadbiran", "lecturer", "pensyarah", "supervisor", "general office", "pejabat am", "bilik pensyarah"]):
            return {
                "reply": (
                    "🏢 **FTMK Administrative & Academic Offices (Block A):**\n\n"
                    "• **Dean's Office (Pejabat Dekan):** Block A, Level 3\n"
                    "• **Academic & Student Affairs Office:** Block A, Level 2\n"
                    "• **Administrative Discussion Room:** Block A, Level 3\n"
                    "• **Main Meeting Room & Seminar Hall:** Block A, Level 4\n\n"
                    "Lecturer consultation rooms are located on Levels 2 and 3 of Block A.\n\n"
                    "Would you like walking directions to the Block A administrative area?"
                ),
                "intent": "FACILITY_INFO",
                "destination_id": "MAIN_ENTRANCE",
            }

        # 9. Study Areas / Group Discussion / Assignment Spaces
        if any(p in msg_lower for p in ["study", "tempat belajar", "group work", "buat assignment", "quiet place", "discussion area", "lepak study", "revision", "tempat bincang"]):
            return {
                "reply": (
                    "📚 **Best Study & Group Discussion Areas inside FTMK:**\n\n"
                    "• **C-ACT (Block A, Level 1):** Student computing & study lounge with air-conditioning, tables, and power outlets.\n"
                    "• **Discussion Rooms (Block A, Levels 2 & 3):** Dedicated rooms for group projects and academic discussion.\n"
                    "• **Students' Common Room (Block D, Level 1):** Relaxed lounge with couches, tables, and vending machines.\n\n"
                    "Would you like walking directions to C-ACT or the Discussion Room?"
                ),
                "intent": "FACILITY_INFO",
                "destination_id": "B_A_L1_C_ACT",
            }

        # 10. Connecting Walkways & Bridges
        if any(p in msg_lower for p in ["bridge", "skybridge", "jambatan", "connecting walkway", "cross block", "lintas blok", "seberang blok"]):
            return {
                "reply": (
                    "🌉 **Connecting Bridges & Walkways between Blocks:**\n\n"
                    "• **Level 2 Skybridge:** Elevated covered walkway directly linking **Block A (Level 2)** and **Block B (Level 2)** — convenient shortcut from admin to AI labs without going downstairs!\n"
                    "• **Level 1 Covered Walkway:** Central walkway connecting the Main Entrance (Block A) to Block B, Block C, Block D, and Block E.\n"
                    "• **Inter-block Corridors:** Direct walkways connect Block B to Block C, and Block E to Block D across Levels 1, 2, 3, and 4.\n\n"
                    "Which block or room are you heading to?"
                ),
                "intent": "FACILITY_INFO",
                "destination_id": None,
            }

        # 11. Lost / Confused Student Guidance
        if any(p in msg_lower for p in ["i am lost", "im lost", "i'm lost", "sesat", "dont know where i am", "don't know where i am", "help me find my way", "where am i"]):
            return {
                "reply": (
                    "🧭 **Don't worry, I'm here to help you find your way!**\n\n"
                    "To locate where you are right now:\n"
                    "1. Look at the wall or nearest door for the **Block Letter** (A, B, C, D, or E).\n"
                    "2. Check the stairwell or doorway sign for the **Level** (Level 1, 2, 3, or 4).\n"
                    "3. Or note down any nearby room name (e.g. *Bilik Kuliah 1*, *AI Lab 1*, or *Main Entrance*).\n\n"
                    "Tell me any room or block you see nearby, and where you want to go — I will guide you with step-by-step walking directions!"
                ),
                "intent": "GENERAL_HELP",
                "destination_id": None,
            }

        # 12. Bot mood / How are you
        if any(p in msg_lower for p in ["how are you", "how r u", "apa khabar", "sihat ke", "how is it going", "how are u"]):
            return {
                "reply": "I'm doing wonderful, thank you for asking! 😊 I'm all set to help you navigate FTMK. What room, lab, or service are you looking for today?",
                "intent": "GENERAL_HELP",
                "destination_id": None,
            }

        # 13. Compliments
        compliment_pattern = r'\b(good job|great job|you (?:are\s+)?(?:so\s+|very\s+)?smart|smart|clever|pandai|terbaik|good bot|nice bot|awesome|cool|hebat|helpful|you are helpful|great assistant)\b'
        if re.search(compliment_pattern, msg_lower):
            return {
                "reply": "Thank you so much! 🥰 I'm always here to make navigating FTMK smooth and effortless. Let me know whenever you need directions or room info!",
                "intent": "GENERAL_HELP",
                "destination_id": None,
            }

        # 14. Vending machines & drinks
        if any(p in msg_lower for p in ["vending machine", "mesin layan diri", "air tin", "coffee machine", "beli air", "buy drink", "mineral water"]):
            return {
                "reply": (
                    "🥤 **Drinks & Vending Machines at FTMK:**\n\n"
                    "• **Drink Vending Machines:** Located at the **Students' Common Room (Block D, Level 1)** and outside the **Block A Main Lobby**.\n"
                    "• **Cold Drinks & Coffee:** Freshly prepared by local food vendors at the **Main Entrance (Block A, Level 1)** during morning and lunch hours.\n\n"
                    "Would you like walking directions to the Students' Common Room or the Main Entrance?"
                ),
                "intent": "FACILITY_INFO",
                "destination_id": "B_D_L1_STUDENTS_COMMON_ROOM",
            }

        return None

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

        # Step -0.3: Casual conversational preambles ("ouhh I see", "oh i see", "ok i see", "alright", etc.)
        preamble_match = re.match(
            r'^(?:ouhh\s+i\s+see|oh\s+i\s+see|ok\s+i\s+see|ouhh\s+see|oh\s+see|alright|ah\s+okay|ouhh|ohh|hmm|well|so|okay)\s*,?\s*',
            message,
            re.I
        )
        if preamble_match:
            remainder = message[preamble_match.end():].strip()
            if remainder:
                message = remainder

        # Step -0.2: Check for change of mind ("actually take me to C-ACT instead", "wait no, where is AI Lab 1?")
        change_match = re.search(r'^(?:actually|instead|no\s+wait|wait\s+no|tak\s+jadi|tukar)\s*,?\s*(?:of\s+that\s*,?\s*)?', message, re.I)
        if change_match:
            session_mem["awaiting_direction_confirmation"] = False
            session_mem["direction_destination"] = None
            remainder = message[change_match.end():].strip()
            if remainder:
                message = remainder

        # Step -0.1: Quick ellipsis switching ("and BK2?", "how about lab 3?", "what about block c?")
        ellipsis_match = re.search(r'^(?:and|how\s+about|what\s+about|macam\s+mana\s+pula)\s+', message, re.I)
        if ellipsis_match:
            remainder = message[ellipsis_match.end():].strip()
            if remainder:
                message = remainder

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

        # Step 0.08: Check for Sequential Multi-Stop Destinations ("bring me to X but first go to Y", "first go to Y then X")
        seq_res = self._handle_sequential_destinations(message, session_mem, current_loc)
        if seq_res:
            self._record_nlp_turn(session_id, message, seq_res["reply"], seq_res.get("entities"))
            seq_res["session_id"] = session_id
            return seq_res

        # Step 0.1: Check for explicit Origin-to-Destination routing ("from A to B", "between A and B", "what good jalan from A to B")
        orig_match, dest_match, orig_cand, dest_cand = self._extract_origin_and_destination(message)
        if orig_cand and dest_cand:
            # Case 1: Both locations exist in FTMK
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

            # Case 2: Starting point found, but destination DOES NOT exist in FTMK (e.g. 'kernal')
            elif orig_match and not dest_match:
                orig_name = orig_match["name"]
                orig_bld = orig_match.get("building", "FTMK")
                orig_flr = orig_match.get("floor", 1)
                reply_text = (
                    f"📍 I recognized your starting location as **{orig_name}** ({orig_bld}, Level {orig_flr}), "
                    f"but **'{dest_cand}'** was not found in the FTMK Faculty.\n\n"
                    f"FTMK consists of 5 main blocks (A, B, C, D, E) across Levels 1 to 4. "
                    f"Please verify the destination room name or tell me what facility you are looking for!"
                )
                self._record_nlp_turn(session_id, message, reply_text)
                return {
                    "reply": reply_text,
                    "intent": "LOCATION_QUERY",
                    "destination_id": None,
                    "confidence": 1.0,
                    "entities": {"destination": dest_cand, "category": None, "building": None},
                    "handoff": None,
                    "route_info": None,
                    "recommendations": None,
                    "session_id": session_id,
                    "error": None,
                }

            # Case 3: Destination found, but starting point DOES NOT exist in FTMK
            elif not orig_match and dest_match:
                dest_name = dest_match["name"]
                dest_bld = dest_match.get("building", "FTMK")
                dest_flr = dest_match.get("floor", 1)
                reply_text = (
                    f"📍 I recognized your destination as **{dest_name}** ({dest_bld}, Level {dest_flr}), "
                    f"but starting location **'{orig_cand}'** was not recognized in FTMK.\n\n"
                    f"Would you like walking directions starting from the **Main Entrance** instead?"
                )
                session_mem["last_destination"] = dest_match
                session_mem["direction_destination"] = dest_match
                session_mem["awaiting_direction_confirmation"] = True
                self._record_nlp_turn(session_id, message, reply_text)
                return {
                    "reply": reply_text,
                    "intent": "LOCATION_QUERY",
                    "destination_id": dest_match["id"],
                    "confidence": 1.0,
                    "entities": {"destination": dest_name, "category": dest_match.get("category"), "building": dest_bld},
                    "handoff": None,
                    "route_info": None,
                    "recommendations": None,
                    "session_id": session_id,
                    "error": None,
                }

        # Step 0.2: Check for Non-Existent Facilities or Invalid Room Numbers (e.g. AI Lab 6, BK 8, ATM, etc.)
        non_exist = self._check_non_existent_facility(message)
        if non_exist:
            self._record_nlp_turn(session_id, message, non_exist["reply"])
            return {
                "reply": non_exist["reply"],
                "intent": non_exist.get("intent", "LOCATION_QUERY"),
                "destination_id": non_exist.get("destination_id"),
                "confidence": 1.0,
                "entities": {"destination": None, "category": None, "building": None},
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "session_id": session_id,
                "error": None,
            }

        # Step 0.25: Check for Faculty / Campus Overview ("what have in ftmk", "in ftmk what facilitity haver", "can you give information about ftmk")
        overview_reply = self._handle_faculty_overview(message)
        if overview_reply:
            self._record_nlp_turn(session_id, message, overview_reply)
            return {
                "reply": overview_reply,
                "intent": "FACILITY_INFO",
                "destination_id": None,
                "confidence": 1.0,
                "entities": {"destination": None, "category": "faculty_overview", "building": None},
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "session_id": session_id,
                "error": None,
            }

        # Step 0.28: Check for Floor / Level queries ("what is on level 2", "what's in block b level 1", "apa ada kat tingkat 3")
        floor_res = self._handle_floor_level_query(message, session_mem)
        if floor_res:
            self._record_nlp_turn(session_id, message, floor_res["reply"], floor_res.get("entities"))
            floor_res["session_id"] = session_id
            return floor_res

        # Step 0.3: Check for Pairwise Proximity Comparison ("kernel room near with bk1?", "is ai lab 1 near bk1?")
        prox_res = self._handle_proximity_comparison(message, session_mem)
        if prox_res:
            self._record_nlp_turn(session_id, message, prox_res["reply"], prox_res.get("entities"))
            prox_res["session_id"] = session_id
            return prox_res

        # Step 0.32: Check for Walking Distance & Estimated Travel Time ("how far is it?", "how long does it take?", "berapa jauh?")
        dist_res = self._handle_distance_time_query(message, session_mem, current_loc)
        if dist_res:
            self._record_nlp_turn(session_id, message, dist_res["reply"], dist_res.get("entities"))
            dist_res["session_id"] = session_id
            return dist_res

        # Step 0.35: Check for Surrounding / Nearby Queries ("what surround ai 1", "what is near X", etc.)
        surround_res = self._handle_surrounding_query(message, session_mem)
        if surround_res:
            self._record_nlp_turn(session_id, message, surround_res["reply"], surround_res.get("entities"))
            surround_res["session_id"] = session_id
            return surround_res

        # Step 0.38: Check for Ordinal Selection from previous options ("take me to the first one", "the second one", "number 1")
        ordinal_res = self._handle_ordinal_selection(message, session_mem, current_loc)
        if ordinal_res:
            ordinal_res["session_id"] = session_id
            self._record_nlp_turn(session_id, message, ordinal_res["reply"], ordinal_res.get("entities"))
            return ordinal_res

        # Step 0.4: Check for Conversational / Small-talk queries ("who are you", "thank you", "wifi", etc.)
        conv_res = self._handle_conversational_questions(message)
        if conv_res:
            self._record_nlp_turn(session_id, message, conv_res["reply"])
            return {
                "reply": conv_res["reply"],
                "intent": conv_res.get("intent", "GENERAL_HELP"),
                "destination_id": conv_res.get("destination_id"),
                "confidence": 1.0,
                "entities": {"destination": None, "category": None, "building": None},
                "handoff": None,
                "route_info": None,
                "recommendations": None,
                "session_id": session_id,
                "error": None,
            }

        # Step 0.5: Check for Affirmative Confirmation or Follow-up Navigation Command (including custom origin e.g. "yes from ai lab3")
        is_aff = self._is_affirmative(message)
        is_nav = self._is_navigation_command(message)

        # Check if the user specified an explicit starting point in this turn:
        # e.g. "yes from ai lab3", "from ai lab 3", "yes start from bk 1", "dari bilik viva"
        origin_from_match = re.search(
            r'\b(?:from|dari|dr|starting\s+from|start\s+from)\s+(.+)', message, re.IGNORECASE
        )
        custom_origin_loc = None
        if origin_from_match:
            raw_orig_text = origin_from_match.group(1).strip().rstrip("?.!,")
            if not re.search(r'\b(?:to|ke|towards)\b', raw_orig_text, re.I):
                custom_origin_loc = self._find_location_in_text(raw_orig_text)
                if not custom_origin_loc:
                    # User specified an origin that does not exist in FTMK!
                    target_dest = session_mem.get("direction_destination") or session_mem.get("last_destination")
                    dest_str = f" to **{target_dest['name']}**" if target_dest else ""
                    reply_text = (
                        f"📍 I would be happy to guide you{dest_str}, but starting location "
                        f"**'{raw_orig_text}'** was not recognized in FTMK.\n\n"
                        f"Would you like walking directions starting from the **Main Entrance** instead?"
                    )
                    self._record_nlp_turn(session_id, message, reply_text)
                    return {
                        "reply": reply_text,
                        "intent": "LOCATION_QUERY",
                        "destination_id": target_dest["id"] if target_dest else None,
                        "confidence": 1.0,
                        "entities": {"destination": target_dest["name"] if target_dest else None, "category": None, "building": None},
                        "handoff": None,
                        "route_info": None,
                        "recommendations": None,
                        "session_id": session_id,
                        "error": None,
                    }

        # Check if user specified a destination directly in text WITHOUT "from"
        direct_loc_check = None
        if not origin_from_match:
            direct_loc_check = self._find_location_in_text(message)

        # Did the user say "can you bring me" / "bring me" with NO location, and NO previous destination in memory?
        if is_nav and not direct_loc_check and not custom_origin_loc and not session_mem.get("last_destination") and not session_mem.get("direction_destination"):
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
        # User confirmed ("yes", "sure", "susre", "ok", "yes from ai lab3") OR requested navigation ("can you bring me", "bring me there")
        if (is_aff or is_nav or (custom_origin_loc and session_mem.get("awaiting_direction_confirmation"))) and (session_mem.get("awaiting_direction_confirmation") or session_mem.get("last_destination")):
            target_dest = direct_loc_check or session_mem.get("direction_destination") or session_mem.get("last_destination")
            if not target_dest and session_mem.get("last_topic") == "library":
                target_dest = self.repository.get("C-ACT") or self.repository.search_by_name("C-ACT")

            if target_dest:
                session_mem["awaiting_direction_confirmation"] = False
                session_mem["last_destination"] = target_dest
                session_mem["last_building"] = target_dest.get("building")
                session_mem["last_topic"] = target_dest.get("category")

                # Determine starting origin:
                # 1. Custom origin explicitly given by user ("yes from ai lab3")
                # 2. Or stored direction_origin from a previous pairwise comparison
                # 3. Or current_loc passed into handle_query
                route_origin_id = current_loc
                if custom_origin_loc:
                    route_origin_id = custom_origin_loc["id"]
                elif session_mem.get("direction_origin") and is_aff:
                    route_origin_id = session_mem["direction_origin"]["id"]
                    session_mem["direction_origin"] = None

                extra_tip = None
                if target_dest.get("id") == "MAIN_ENTRANCE" or session_mem.get("last_topic") == "food":
                    extra_tip = "Once you arrive at the lobby on Level 1, the food vendors (selling Nasi Lemak, Karipap, Pau, snacks & drinks) are set up right near the entrance!"

                res = self._build_walking_directions_response(route_origin_id, target_dest, extra_tip)
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
                    rec_objs = []
                    for r in recommendations_list:
                        obj = self.repository.get(r.get("destination_id")) or self.repository.search_by_name(r.get("name", ""))
                        if obj:
                            rec_objs.append(obj)
                    if rec_objs:
                        session_mem["last_options_list"] = rec_objs

                    recs_text = "\n".join(
                        f"• **{r['name']}** — {r.get('building', '')}, Level {r.get('floor', '')}"
                        for r in recommendations_list[:4]
                    )
                    reply = (
                        f"💡 **Recommended destinations for your request:**\n\n"
                        f"{recs_text}\n\n"
                        f"Would you like walking directions to the first one, or another specific room?"
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

        # Step 9.5: Safeguard for location queries that did not match any place in FTMK
        elif any(kw in msg_lower for kw in ["where is", "where are", "where", "kat mana", "kat mane", "mana", "di mana", "how to get to", "cari", "find"]):
            query_target = raw_dest or re.sub(
                r'\b(where is|where are|where|kat mana|kat mane|mana|di mana|how to get to|how do i get to|find|cari|the|show me|tell me|room|lab)\b',
                '',
                msg_lower
            ).strip()
            if query_target and len(query_target) >= 2:
                reply = (
                    f"📍 **'{query_target}' was not found in the FTMK Faculty.**\n\n"
                    f"FTMK consists of 5 main connected blocks (Blocks A, B, C, D, and E) across Levels 1 to 4. "
                    f"Please double-check the room name or let me know what faculty facility you are searching for!"
                )

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
