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

import difflib
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List, Set


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
        r'\bsurrond\b': 'surround',
        r'\bsuround\b': 'surround',
        r'\bjln\b': 'jalan',
        r'\bfacilitity\b': 'facility',
        r'\bfaciltiy\b': 'facility',
        r'\bhaver\b': 'have',
        r'\bkernal\b': 'kernel',
        r'\binfo\b': 'information',
        r'\bfaculti\b': 'faculty',
        r'\bfakulti\b': 'faculty',
        r'\bnear\s+with\b': 'near',
        r'\bclose\s+with\b': 'close to',
        r'\bsebelah\s+dengan\b': 'sebelah',
        r'\bdekat\s+dengan\b': 'dekat',

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

    # Speech-To-Text (STT) phonetic corrections for acoustic slips
    SPEECH_TO_TEXT_CORRECTIONS = [
        # Class vs Glass acoustic slips (minimal pair: /klæs/ vs /glæs/)
        (r'\bsurrounding\s+glass(?:es)?\b', 'surrounding class'),
        (r'\bglass\s*rooms?\b', 'classroom'),
        (r'\b(?:in|at|near|beside|into)\s+glass(?:es)?\b', 'in class'),
        (r'\bglass\b', 'class'),
        (r'\bglasses\b', 'classes'),
        # Bilik Kuliah / BK acoustic slips
        (r'\bbilly\s*kulia\s*(?:to|too|two)\b', 'bilik kuliah 2'),
        (r'\bbilly\s*kulia\s*(?:tree|free|three)\b', 'bilik kuliah 3'),
        (r'\bbilly\s*kulia\s*(?:tour|for|door|four)\b', 'bilik kuliah 4'),
        (r'\bbilly\s*kulia\s*(?:that|dat)\s*one\b', 'bilik kuliah 1'),
        (r'\bbilly\s*kulia\s*([0-9]{1,2})\b', r'bilik kuliah \1'),
        (r'\bbilly\s*kulia\b', 'bilik kuliah'),
        (r'\bbillie\s*kulia\b', 'bilik kuliah'),
        (r'\bbilly\s*clear\b', 'bilik clear'),
        # Dewan Kuliah / DK acoustic slips
        (r'\b(?:where\s+did\s+europe|where\s+do\s+you\s+and\s+europe)\b', 'where is dewan kuliah'),
        (r'\b(?:the\s+one\s+cool\s+yeah|the\s+one\s+kulia)\b', 'dewan kuliah'),
        (r'\b(?:die\s*k|day\s*k)\b', 'dk'),
        (r'\b(?:bee\s*k|be\s*k)\b', 'bk'),
        # Programming Lab acoustic slips
        (r'\bprogram\s+(?:that|dat)\s*one\b', 'programming lab 1'),
        (r'\bprog(?:ram(?:ming)?)?\s*lab\s+(?:that|dat)\s*one\b', 'programming lab 1'),
        (r'\bprogram\s+that\s+two\b', 'programming lab 2'),
        # AI Lab acoustic slips
        (r'\bai\s+lab\s+(?:tour|for|door)\b', 'ai lab 4'),
        (r'\bai\s+lab\s+(?:to|too)\b', 'ai lab 2'),
        (r'\bai\s+lab\s+(?:tree|free)\b', 'ai lab 3'),
        (r'\b(?:eye|ay)\s+lab\s*([1-4])\b', r'ai lab \1'),
        # Makmal phonetic slips
        (r'\b(?:mac\s*mall|mak\s*mal|muck\s*mall)\b', 'makmal'),
        # Multimedia Lab slips
        (r'\bmulti(?:media)?\s*(?:lab\s*)?(?:tour|for|door)\b', 'multimedia lab 4'),
        (r'\bmulti(?:media)?\s*(?:lab\s*)?(?:to|too)\b', 'multimedia lab 2'),
        (r'\bmulti(?:media)?\s*(?:lab\s*)?(?:tree|free)\b', 'multimedia lab 3'),
        (r'\bmulti(?:media)?\s*(?:lab\s*)?(?:that|dat)\s*one\b', 'multimedia lab 1'),
        # C-ACT slips
        (r'\b(?:see\s*act|sea\s*act|c\s*act)\b', 'c-act'),
    ]

    # Contractions and room abbreviations
    ABBREVIATION_PATTERNS = [
        # Programming Lab
        (r'\b(?:makmal\s*(?:program(?:ming)?|pengaturcaraan)|prog(?:ram(?:ming)?)?\s*lab(?:oratory)?)\s*([1-4])\b', r'programming lab \1'),
        (r'\b(?:makmal\s*(?:program(?:ming)?|pengaturcaraan)|prog(?:ram(?:ming)?)?\s*lab(?:oratory)?)\b(?!\s*[0-9])', 'programming lab 1'),
        # AI Lab
        (r'\b(?:makmal\s*ai|ai\s*lab(?:oratory)?|ai)\s*([1-4])\b', r'ai lab \1'),
        (r'\b(?:makmal\s*ai|ai\s*lab(?:oratory)?)\b(?!\s*[0-9])', 'ai lab 1'),
        # Database Lab
        (r'\b(?:makmal\s*(?:pangkalan\s*data|database)|(?:data(?:base)?|db)\s*lab(?:oratory)?)\s*([1-3])\b', r'database lab \1'),
        (r'\b(?:makmal\s*(?:pangkalan\s*data|database)|(?:data(?:base)?|db)\s*lab(?:oratory)?)\b(?!\s*[0-9])', 'database lab 1'),
        # Software Engineering Lab
        (r'\b(?:makmal\s*kejuruteraan\s*perisian|(?:soft(?:ware)?\s*eng(?:ineering)?|se)\s*lab(?:oratory)?)\s*([1-3])\b', r'software engineering lab \1'),
        (r'\b(?:makmal\s*kejuruteraan\s*perisian|(?:soft(?:ware)?\s*eng(?:ineering)?|se)\s*lab(?:oratory)?)\b(?!\s*[0-9])', 'software engineering lab 1'),
        # Multimedia Lab
        (r'\b(?:makmal\s*multimedia|(?:multi(?:media)?|mm)\s*lab(?:oratory)?)\s*([1-4])\b', r'multimedia lab \1'),
        (r'\b(?:makmal\s*multimedia|(?:multi(?:media)?|mm)\s*lab(?:oratory)?)\b(?!\s*[0-9])', 'multimedia lab 1'),
        # Network Lab
        (r'\b(?:makmal\s*rangkaian|(?:net(?:work)?)\s*lab(?:oratory)?)\s*([1-2])\b', r'network lab \1'),
        (r'\b(?:makmal\s*rangkaian|(?:net(?:work)?)\s*lab(?:oratory)?)\b(?!\s*[0-9])', 'network lab 1'),
        # Lecture Rooms (BK 1 - 16)
        (r'\b(?:lec(?:ture)?\s*room|bilik\s*kuliah|bk)\s*([0-9]{1,2})\b', r'lecture room \1'),
        (r'\bdewan\s*seminar\b', 'seminar hall'),
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
        (r'\b(?:bilik\s+)?clear(?:\s+room)?\b', 'clear room'),
    ]

    # Vocal filler words and hesitation noises (English & Malay)
    FILLER_PATTERNS = [
        r'\b(?:u+h+m*|u+m+|h+m+|e+r+m*|a+h+|e+h+|e+m+|a+a+)\b',
        r'\[(?:music|applause|laughter|silence|sigh|cough|throat-clearing|groan|bell)\]',
        r'\((?:music|applause|laughter|silence|sigh|cough|throat-clearing|groan|bell)\)',
    ]

    # Spoken number conversion (English & Malay -> digits)
    NUMBER_WORD_MAP = [
        (r'\bsebelas\b', '11'),
        (r'\bdua\s*belas\b', '12'),
        (r'\btiga\s*belas\b', '13'),
        (r'\bempat\s*belas\b', '14'),
        (r'\blima\s*belas\b', '15'),
        (r'\benam\s*belas\b', '16'),
        (r'\beleven\b', '11'),
        (r'\btwelve\b', '12'),
        (r'\bthirteen\b', '13'),
        (r'\bfourteen\b', '14'),
        (r'\bfifteen\b', '15'),
        (r'\bsixteen\b', '16'),
        (r'\b(?:zero|sifar|kosong)\b', '0'),
        (r'\b(?:one|first|satu|pertama)\b', '1'),
        (r'\b(?:two|second|dua|kedua)\b', '2'),
        (r'\b(?:three|third|tiga|ketiga)\b', '3'),
        (r'\b(?:four|fourth|empat|keempat)\b', '4'),
        (r'\b(?:five|fifth|lima|kelima)\b', '5'),
        (r'\b(?:six|sixth|enam|keenam)\b', '6'),
        (r'\b(?:seven|seventh|tujuh|ketujuh)\b', '7'),
        (r'\b(?:eight|eighth|lapan|kelapan)\b', '8'),
        (r'\b(?:nine|ninth|sembilan|kesembilan)\b', '9'),
        (r'\b(?:ten|tenth|sepuluh|kesepuluh)\b', '10'),
    ]

    # Stopwords protected from accidental similarity mutation
    STOPWORDS = {
        'what', 'whats', 'what\'s', 'which', 'where', 'wheres', 'who', 'how',
        'does', 'do', 'did', 'is', 'are', 'was', 'were', 'have', 'has', 'had',
        'in', 'at', 'on', 'the', 'a', 'an', 'to', 'for', 'from', 'of', 'with',
        'and', 'or', 'so', 'can', 'could', 'would', 'should', 'will',
        'i', 'me', 'my', 'you', 'your', 'it', 'its', 'there', 'this', 'that'
    }

    # Core campus environment vocabulary base
    STATIC_DOMAIN_VOCABULARY = {
        "class", "classes", "classroom", "classrooms", "lab", "labs", "laboratory",
        "lecture", "hall", "room", "rooms", "programming", "software", "network",
        "database", "multimedia", "robotics", "artificial", "intelligence", "viva",
        "seminar", "surrounding", "building", "level", "floor", "facility", "facilities",
        "corridor", "bridge", "toilet", "restroom", "library", "cafeteria", "office",
        "direction", "directions", "entrance", "block", "path", "shortest", "nearest"
    }

    _cached_domain_vocabulary: Optional[Set[str]] = None
    _cached_vocab_skeletons: Optional[Dict[str, str]] = None

    @classmethod
    def phonetic_skeleton(cls, word: str) -> str:
        """
        Acoustic-phonetic consonant skeleton normalizer (Metaphone/Soundex hybrid).
        Normalizes voicing pairs (/k/ vs /g/, /p/ vs /b/, /t/ vs /d/, /f/ vs /v/)
        so acoustic speech slips produce identical phonetic hashes.
        """
        if not word:
            return ""
        w = word.lower().strip()
        w = w.replace('ph', 'f').replace('th', 't').replace('ck', 'k').replace('dg', 'j').replace('wh', 'w')
        charmap = {'c': 'k', 'q': 'k', 'g': 'k', 'p': 'b', 't': 'd', 'v': 'f', 'z': 's', 'j': 'ch', 'y': 'i'}
        res = []
        for i, ch in enumerate(w):
            mapped = charmap.get(ch, ch)
            if i > 0 and mapped in 'aeiou':
                continue
            if not res or res[-1] != mapped:
                res.append(mapped)
        return ''.join(res)

    @classmethod
    def get_domain_vocabulary(cls) -> Tuple[Set[str], Dict[str, str]]:
        """
        Dynamically extracts and caches the full campus vocabulary and phonetic skeletons
        from both static keywords and locations.json (Block A to E).
        """
        if cls._cached_domain_vocabulary is not None and cls._cached_vocab_skeletons is not None:
            return cls._cached_domain_vocabulary, cls._cached_vocab_skeletons

        vocab = set(cls.STATIC_DOMAIN_VOCABULARY)
        try:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parent
            loc_file = repo_root / "module_1_back_end" / "backend" / "knowledge_base" / "data" / "locations.json"
            if loc_file.exists():
                with open(loc_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    locs = data.get("locations", []) if isinstance(data, dict) else data
                    for loc in locs:
                        sources = [
                            loc.get("name", ""),
                            loc.get("category", ""),
                            loc.get("building", ""),
                        ] + loc.get("aliases", []) + loc.get("keywords", [])
                        for s in sources:
                            for token in re.findall(r'[a-zA-Z0-9]+', s.lower()):
                                if len(token) >= 2:
                                    vocab.add(token)
        except Exception:
            pass

        skeletons = {w: cls.phonetic_skeleton(w) for w in vocab}
        cls._cached_domain_vocabulary = vocab
        cls._cached_vocab_skeletons = skeletons
        return vocab, skeletons

    @classmethod
    def align_to_domain_vocabulary(cls, text: str, threshold: float = 0.80) -> str:
        """
        High-Accuracy NLP Hybrid Aligner:
        Combines 50% orthographic similarity (difflib) + 50% acoustic phonetic skeleton match.
        Guarantees accurate projection of speech slips ('glass' -> 'class', 'lap' -> 'lab',
        'lectur' -> 'lecture') into the campus domain vocabulary in <1ms without high memory overhead.
        """
        if not text:
            return ""

        vocab, vocab_skeletons = cls.get_domain_vocabulary()
        tokens = text.split()
        corrected_tokens = []

        for token in tokens:
            lower_token = token.lower()
            # Fast pass: exact matches, protected stopwords, or tiny words
            if lower_token in vocab or lower_token in cls.STOPWORDS or len(lower_token) <= 2:
                corrected_tokens.append(token)
                continue

            t_sk = cls.phonetic_skeleton(lower_token)
            best_cand = None
            best_score = threshold

            # Compare against domain vocabulary with length filter
            for cand, c_sk in vocab_skeletons.items():
                if abs(len(cand) - len(lower_token)) > 2:
                    continue
                s_ortho = difflib.SequenceMatcher(None, lower_token, cand).ratio()
                s_phone = difflib.SequenceMatcher(None, t_sk, c_sk).ratio()
                score = 0.5 * s_ortho + 0.5 * s_phone
                if score > best_score:
                    best_score = score
                    best_cand = cand

            if best_cand:
                rep = best_cand
                if token.isupper():
                    rep = rep.upper()
                elif token.istitle():
                    rep = rep.capitalize()
                corrected_tokens.append(rep)
            else:
                corrected_tokens.append(token)

        return " ".join(corrected_tokens)

    @classmethod
    def get_preferred_name(cls, raw_name: str, prefer_english: bool = True) -> str:
        """
        Returns location name formatted according to language preference.
        If prefer_english and name has a '/' (bilingual), returns English name first.
        """
        if not raw_name or "/" not in raw_name:
            return raw_name

        parts = [p.strip() for p in raw_name.split("/")]
        if len(parts) != 2:
            return raw_name

        p0, p1 = parts[0], parts[1]
        malay_indicators = ["makmal", "bilik", "dewan", "tandas", "lobi", "pusat", "penyelidikan", "aras"]
        p0_is_malay = any(ind in p0.lower() for ind in malay_indicators)
        p1_is_malay = any(ind in p1.lower() for ind in malay_indicators)

        if p0_is_malay and not p1_is_malay:
            malay_part, eng_part = p0, p1
        elif p1_is_malay and not p0_is_malay:
            malay_part, eng_part = p1, p0
        else:
            malay_part, eng_part = p0, p1

        if prefer_english:
            return f"{eng_part} ({malay_part})"
        else:
            return f"{malay_part} ({eng_part})"

    @classmethod
    def preprocess_text(cls, text: str) -> str:
        """
        Cleans, fixes typos, corrects speech-to-text slips, strips fillers, and expands abbreviations.
        """
        if not text:
            return ""

        s = text.lower().strip()

        # 0. Strip vocal hesitation / filler sounds (uh, um, hmm, er, etc.)
        for pattern in cls.FILLER_PATTERNS:
            s = re.sub(pattern, ' ', s, flags=re.IGNORECASE)

        # Clean isolated ellipses or leading punctuation left over by filler words
        s = re.sub(r'[\.\,]+', ' ', s)

        # 1. Convert spoken number words to digits (English & Malay)
        for pattern, replacement in cls.NUMBER_WORD_MAP:
            s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)

        # 2. Apply speech-to-text acoustic corrections
        for pattern, replacement in cls.SPEECH_TO_TEXT_CORRECTIONS:
            s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)

        # 3. Apply typo corrections
        for pattern, replacement in cls.TYPO_CORRECTIONS.items():
            s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)

        # 4. Apply domain vocabulary alignment (NLP Word Similarity)
        s = cls.align_to_domain_vocabulary(s)

        # 5. Expand abbreviations
        for pattern, replacement in cls.ABBREVIATION_PATTERNS:
            s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)

        # Normalize multiple spaces
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    @classmethod
    def correct_speech_transcript(cls, transcript: str) -> str:
        """
        Dedicated speech post-processing layer:
        Repairs acoustic slips, homophones, and campus terminology in raw transcripts.
        """
        return cls.preprocess_text(transcript)

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
            # 1. "to <dest> after [my class/class/event at] <orig>"
            r'(?:.*?\b)?(?:to|ke|towards|head\s+to|walk\s+to|go\s+to|visit)\s+(.+?)\s+(?:after|lepas|selepas)\s+(?:(?:my\s+)?(?:class|lab|lecture|event)\s+(?:at|in|kat|dekat)\s+)?(.+)',
            # 2. "after [my class/class/event at] <orig> ... <dest>"
            r'(?:.*?\b)?(?:after|lepas|selepas)\s+(?:(?:my\s+)?(?:class|lab|lecture|event)\s+(?:at|in|kat|dekat)\s+)?(.+?)(?:,|\s+then|\s+and|\s+so)?\s+(?:i\s+want\s+to\s+go\s+to|i\s+need\s+to\s+go\s+to|how\s+to\s+go\s+to|how\s+do\s+i\s+get\s+to|how\s+can\s+i\s+get\s+to|take\s+me\s+to|bring\s+me\s+to|guide\s+me\s+to|go\s+to|head\s+to|walk\s+to|nak\s+pergi\s+ke|nak\s+ke|to|ke)\s+(.+)',
            # 3. "I am at / currently at / starting from <orig> ... <dest>"
            r'(?:.*?\b)?(?:i\s+am\s+at|i\'m\s+at|im\s+at|currently\s+at|saya\s+di|saya\s+kat|start\s+(?:at|from)|starting\s+(?:at|from))\s+(.+?)(?:,|\s+then|\s+and|\s+so)?\s+(?:how\s+(?:to|do\s+i|can\s+i)\s+(?:get|go|walk)\s+to|take\s+me\s+to|bring\s+me\s+to|guide\s+me\s+to|i\s+want\s+to\s+go\s+to|go\s+to|walk\s+to|head\s+to|nak\s+pergi\s+ke|nak\s+ke|to|ke)\s+(.+)',
            # 4. "from <origin> to <dest>"
            r'\b(?:from|dari)\s+(.+?)\s+(?:to|ke|towards|sampai)\s+(.+)',
            # 5. "between <origin> and <dest>"
            r'\b(?:between|antara)\s+(.+?)\s+(?:and|dan|with|dengan)\s+(.+)',
            # 6. "<dest> from <origin>"
            r'\b(?:to|ke|towards)\s+(.+?)\s+(?:from|dari)\s+(.+)',
            # 7. Direct "<origin> to <dest>"
            r'^(?:can\s+you\s+)?(?:show\s+(?:me\s+)?)?(?:short\s+|shortest\s+|nearest\s+)?(?:path\s+|route\s+)?(?:from\s+)?(.+?)\s+(?:to|ke|towards)\s+(.+)$',
        ]

        for idx, pattern in enumerate(patterns):
            match = re.search(pattern, clean, re.IGNORECASE)
            if match:
                g1, g2 = match.group(1).strip(), match.group(2).strip()
                if idx in (0, 5):  # dest, orig
                    dest_cand, orig_cand = g1, g2
                else:  # orig, dest
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
