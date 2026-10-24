"""
Campus NLP Engine
=================
Deterministic, high-performance Natural Language Processing module for campus navigation.
Handles:
1. Spelling correction & typo fixing (e.g. 'short part' -> 'short path', 'toliet' -> 'toilet')
2. Stemming, plural/singular normalization & room abbreviations
3. Longest-alias-first campus entity resolution (prevents substring collision bugs)
4. Flexible Origin-to-Destination semantic slot extraction
"""

import re
from typing import Optional, Dict, Any, Tuple, List


class CampusNLP:
    """Production NLP preprocessor and entity resolution engine."""

    # Common navigation, intent, and campus typos
    TYPO_CORRECTIONS = {
        # Navigation / path typos
        r'\bshort\s+part\b': 'short path',
        r'\bshot\s+path\b': 'short path',
        r'\bshrot\s+path\b': 'short path',
        r'\bsort\s+path\b': 'short path',
        r'\bfastes\b': 'fastest',
        r'\bquickes\b': 'quickest',
        r'\bdirecsion\b': 'direction',
        r'\bderiction\b': 'direction',
        r'\bdirection\b': 'direction',
        r'\bdirections\b': 'directions',
        r'\bderictions\b': 'directions',
        r'\bdirecsions\b': 'directions',
        r'\bwalkin\b': 'walking',
        r'\bguid\b': 'guide',
        r'\bguidence\b': 'guidance',

        # Facility / amenity typos
        r'\btoliet\b': 'toilet',
        r'\btoilete\b': 'toilet',
        r'\btoliets\b': 'toilets',
        r'\brestrom\b': 'restroom',
        r'\brestroms\b': 'restrooms',
        r'\bwashrom\b': 'washroom',
        r'\blibary\b': 'library',
        r'\blibrari\b': 'library',
        r'\bperpus\b': 'perpustakaan',
        r'\bcafetaria\b': 'cafeteria',
        r'\bmakml\b': 'makmal',
        r'\blabratory\b': 'laboratory',
        r'\blabrotory\b': 'laboratory',

        # Campus room names & spelling errors
        r'\bsysem\b': 'systems',
        r'\bsytem\b': 'systems',
        r'\bsistem\b': 'systems',
        r'\bprogam\b': 'programming',
        r'\bprogrem\b': 'programming',
        r'\bprograming\b': 'programming',
        r'\bmultimeda\b': 'multimedia',
        r'\bsoft\s*eng\b': 'software engineering',
        r'\bsoft\s*ware\b': 'software',
        r'\bdatbase\b': 'database',
        r'\bdatabse\b': 'database',
        r'\bnetwrok\b': 'network',
        r'\blectur\b': 'lecture',
        r'\blecktur\b': 'lecture',
        r'\bseminr\b': 'seminar',
        r'\bmeetin\b': 'meeting',
    }

    # Contractions and room abbreviations
    ABBREVIATION_PATTERNS = [
        # Programming Lab
        (r'\bprog(?:ram(?:ming)?)?\s*(?:lab(?:oratory)?)?\s*([1-4])\b', r'programming lab \1'),
        (r'\bmakmal\s*program(?:ming)?\s*([1-4])\b', r'makmal pengaturcaraan \1'),
        # AI Lab
        (r'\bai\s*(?:lab(?:oratory)?)?\s*([1-4])\b', r'ai lab \1'),
        # Database Lab
        (r'\b(?:data(?:base)?|db)\s*(?:lab(?:oratory)?)?\s*([1-3])\b', r'database lab \1'),
        # Software Engineering Lab
        (r'\b(?:soft(?:ware)?\s*eng(?:ineering)?|se)\s*(?:lab(?:oratory)?)?\s*([1-3])\b', r'software engineering lab \1'),
        # Multimedia Lab
        (r'\b(?:multi(?:media)?|mm)\s*(?:lab(?:oratory)?)?\s*([1-4])\b', r'multimedia lab \1'),
        # Network Lab
        (r'\b(?:net(?:work)?)\s*(?:lab(?:oratory)?)?\s*([1-2])\b', r'network lab \1'),
        # Lecture Rooms (BK 1 - 16)
        (r'\b(?:lec(?:ture)?\s*room|bilik\s*kuliah|bk)\s*([0-9]{1,2})\b', r'lecture room \1'),
        # Audio Recording Room
        (r'\b(?:audio\s*recording|rakaman\s*audio)\s*(?:room)?\s*([1-2])\b', r'audio recording room \1'),
        # Systems Lab vs Systems and Hardware Lab
        (r'\bsystem\s*and\s*hardware\s*(?:lab)?\b', 'systems and hardware lab'),
        (r'\bsystem\s*lab\b', 'systems lab'),
        # Common Facilities
        (r'\brobot(?:ic(?:s)?)?\s*lab\b', 'robotics lab'),
        (r'\bvr\s*lab\b', 'virtual reality lab'),
        (r'\bgames?\s*lab\b', 'computer games lab'),
        (r'\bcommon\s*room\b', "students common room"),
        (r'\bdiscussion\s*room\b', 'discussion room'),
        (r'\bbincang\b', 'discussion room'),
        (r'\bseminar\s*(?:hall|room)?\b', 'seminar hall'),
        (r'\bexam\s*hall\b', 'seminar hall'),
        (r'\bviva\s*(?:room)?\b', 'viva room'),
        (r'\bmeeting\s*room\b', 'main meeting room'),
        (r'\bcact\b', 'c-act'),
    ]

    @classmethod
    def preprocess_text(cls, text: str) -> str:
        """
        Cleans, fixes typos, and expands abbreviations in user input.
        """
        if not text:
            return ""

        s = text.lower().strip()

        # 1. Apply typo corrections
        for pattern, replacement in cls.TYPO_CORRECTIONS.items():
            s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)

        # 2. Expand abbreviations
        for pattern, replacement in cls.ABBREVIATION_PATTERNS:
            s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)

        # Normalize multiple spaces
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    @classmethod
    def is_navigation_intent(cls, text: str) -> bool:
        """
        Detects whether user is commanding navigation or asking for a route/path.
        Resilient against typos like 'short part', 'fastes way', etc.
        """
        clean = cls.preprocess_text(text)
        patterns = [
            r'\bbring me\b',
            r'\btake me\b',
            r'\bguide me\b',
            r'\blead me\b',
            r'\bshow me\b',
            r'\bshow (?:the )?way\b',
            r'\bshow (?:the )?directions?\b',
            r'\bshow (?:me )?(?:the )?(?:short|shortest|nearest|closest|fastest|quickest)?\s*(?:path|route|way)\b',
            r'\b(?:short|shortest|nearest|closest|fastest|quickest)\s+(?:path|route|way)\b',
            r'\bwalking directions?\b',
            r'\bwalk to\b',
            r'\bhow (?:to|do i|can i)\s+(?:get|go|walk)\s+to\b',
            r'\bdirections?\s+to\b',
            r'\broute\s+to\b',
            r'\bpath\s+to\b',
            r'\bjalan ke\b',
            r'\bnak ke\b',
            r'\bbawa saya\b',
            r'\btunjukkan jalan\b',
        ]
        return any(re.search(p, clean, re.IGNORECASE) for p in patterns)

    @classmethod
    def find_location(cls, text: str, repository: Any) -> Optional[Dict[str, Any]]:
        """
        Finds a campus location using longest-alias-first resolution and stemming.
        Guarantees that specific names like 'Network Lab 1' are never misidentified
        by generic substrings.
        """
        if not text or not repository:
            return None

        clean = cls.preprocess_text(text)
        raw_clean = text.strip()

        # 1. Exact match on repository
        exact = repository.search_by_name(raw_clean) or repository.search_by_name(clean)
        if exact:
            return exact

        # 2. Longest-alias-first match
        # Collect all (alias, location) pairs across the entire database
        all_locs = repository.get_all()
        alias_pairs: List[Tuple[str, Dict[str, Any]]] = []

        for loc in all_locs:
            # Add full name
            alias_pairs.append((loc["name"].lower(), loc))
            # Split bilingual name if available
            if "/" in loc["name"]:
                for part in loc["name"].split("/"):
                    alias_pairs.append((part.strip().lower(), loc))
            # Add all aliases
            for a in loc.get("aliases", []):
                alias_pairs.append((a.strip().lower(), loc))

        # Sort strictly by length of alias in descending order (longest match wins!)
        alias_pairs.sort(key=lambda x: len(x[0]), reverse=True)

        # Check in both preprocessed text and raw lower text
        search_candidates = [clean, raw_clean.lower()]

        for search_str in search_candidates:
            for alias_text, loc in alias_pairs:
                if len(alias_text) < 3:
                    continue
                # Word-boundary search
                if re.search(r'\b' + re.escape(alias_text) + r'\b', search_str):
                    return loc

        # 3. Direct Block gateway mapping if user mentions an entire block
        block_match = re.search(r'\bblock\s+([a-e])\b', clean)
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
                gw = repository.get(gateways[b_letter])
                if gw:
                    return gw

        # 4. Fallback keyword search
        results = repository.search(clean) or repository.search(raw_clean)
        if results:
            return results[0]

        return None

    @classmethod
    def extract_origin_and_destination(
        cls, message: str, repository: Any
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Extracts both origin and destination from user queries, handling typos and variations.
        """
        if not message or not repository:
            return None, None

        clean = cls.preprocess_text(message).rstrip("?.!,")

        patterns = [
            # 1. "from <origin> to <dest>"
            r'\b(?:from|dari)\s+(.+?)\s+(?:to|ke|towards|sampai)\s+(.+)',
            # 2. "between <origin> and <dest>"
            r'\b(?:between|antara)\s+(.+?)\s+(?:and|dan|with|dengan)\s+(.+)',
            # 3. "<dest> from <origin>"
            r'\b(?:to|ke|towards)\s+(.+?)\s+(?:from|dari)\s+(.+)',
            # 4. Direct "<origin> to <dest>"
            r'^(?:can\s+you\s+)?(?:show\s+(?:me\s+)?)?(?:short\s+|shortest\s+|nearest\s+)?(?:path\s+|route\s+)?(?:from\s+)?(.+?)\s+(?:to|ke|towards)\s+(.+)$',
        ]

        for idx, pattern in enumerate(patterns):
            match = re.search(pattern, clean, re.IGNORECASE)
            if match:
                g1, g2 = match.group(1).strip(), match.group(2).strip()
                if idx == 2:
                    dest_cand, orig_cand = g1, g2
                else:
                    orig_cand, dest_cand = g1, g2

                # Strip navigational filler words
                filler = r'\b(please|pls|can you|can i|could you|show me|tell me|give me|short|shortest|nearest|fastest|quickest|path|route|way|walk|how to get|how do i get)\b'
                orig_clean = re.sub(filler, '', orig_cand, flags=re.I).strip()
                dest_clean = re.sub(filler, '', dest_cand, flags=re.I).strip()

                orig_loc = cls.find_location(orig_clean, repository) or cls.find_location(orig_cand, repository)
                dest_loc = cls.find_location(dest_clean, repository) or cls.find_location(dest_cand, repository)

                if orig_loc and dest_loc:
                    return orig_loc, dest_loc

        return None, None
