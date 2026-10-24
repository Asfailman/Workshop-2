"""
Module 2 — AI Recommendation Engine
====================================
Intelligent destination recommendation using a weighted scoring algorithm.

This module receives the user's intent, extracted entities, and free-text
query from Module 1's NLP output and returns a ranked list of suitable
destinations from the knowledge base.

Scoring Strategy:
    The engine computes a composite score for each destination using
    multiple weighted signals:

    1. EXACT NAME MATCH   (weight: 40)  — destination name or alias matches
    2. CATEGORY MATCH     (weight: 30)  — category matches user's request
    3. KEYWORD OVERLAP    (weight: 20)  — overlap between user keywords and
                                          destination keywords/purposes
    4. FUZZY TEXT MATCH   (weight: 10)  — character-level similarity between
                                          query and destination metadata

    Destinations are ranked by descending score. The top-ranked destination
    is the primary recommendation; the rest are alternatives.

Author: Member 2 (AI Recommendation)
"""

from difflib import SequenceMatcher
from typing import Optional

from .knowledge_base import KnowledgeBase


# ---------------------------------------------------------------------------
# Scoring weights (total = 100)
# ---------------------------------------------------------------------------
WEIGHT_EXACT_NAME = 40      # Exact or alias match against destination name
WEIGHT_CATEGORY = 30        # Category match
WEIGHT_KEYWORD = 20         # Keyword / purpose overlap
WEIGHT_FUZZY = 10           # Character-level fuzzy text similarity

# Minimum score threshold to qualify as a valid recommendation
MIN_SCORE_THRESHOLD = 5.0

# Maximum number of recommendations to return
MAX_RECOMMENDATIONS = 5


class RecommendationEngine:
    """
    AI Recommendation Engine — ranks destinations using a weighted
    multi-signal scoring algorithm.

    Usage:
        engine = RecommendationEngine()
        results = engine.recommend(
            query="I need to print my assignment",
            category="printing",
            destination=None,
            building=None,
        )
    """

    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        self.kb = knowledge_base or KnowledgeBase()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend(
        self,
        query: str = "",
        category: Optional[str] = None,
        destination: Optional[str] = None,
        building: Optional[str] = None,
    ) -> dict:
        """
        Generate ranked destination recommendations.

        Args:
            query:       The user's original natural-language request.
            category:    Category extracted by Module 1 NLP (e.g., "printing").
            destination: Specific destination extracted by NLP (e.g., "Library").
            building:    Building constraint extracted by NLP (e.g., "Block A").

        Returns:
            dict with:
                - "recommendations": list of scored destinations (top N)
                - "top_match": the best recommendation (or None)
                - "total_found": total number of destinations scored above threshold
                - "query_info": echo of the input parameters
        """
        all_destinations = self.kb.get_all()

        if not all_destinations:
            return self._empty_result(query, category, destination, building,
                                      reason="No destinations available in knowledge base.")

        # Tokenise the user query for keyword matching
        query_tokens = self._tokenize(query)

        # Score every destination
        scored = []
        for dest in all_destinations:
            score, breakdown = self._score_destination(
                dest=dest,
                query=query,
                query_tokens=query_tokens,
                category=category,
                destination_name=destination,
                building=building,
            )
            if score >= MIN_SCORE_THRESHOLD:
                scored.append({
                    "destination_id": dest["id"],
                    "name": dest["name"],
                    "category": dest.get("category", ""),
                    "building": dest.get("building", ""),
                    "floor": dest.get("floor", ""),
                    "room_number": dest.get("room_number"),
                    "description": dest.get("description", ""),
                    "opening_hours": dest.get("opening_hours", {}),
                    "score": round(score, 2),
                    "score_breakdown": breakdown,
                })

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        # Trim to top N
        top_results = scored[:MAX_RECOMMENDATIONS]

        return {
            "recommendations": top_results,
            "top_match": top_results[0] if top_results else None,
            "total_found": len(scored),
            "query_info": {
                "query": query,
                "category": category,
                "destination": destination,
                "building": building,
            },
        }

    # ------------------------------------------------------------------
    # Scoring algorithm
    # ------------------------------------------------------------------

    def _score_destination(
        self,
        dest: dict,
        query: str,
        query_tokens: set[str],
        category: Optional[str],
        destination_name: Optional[str],
        building: Optional[str],
    ) -> tuple[float, dict]:
        """
        Compute the composite score for a single destination.

        Returns:
            (total_score, breakdown_dict)
        """
        breakdown = {}
        total = 0.0

        # ----- 1. EXACT NAME MATCH (weight: 40) -----
        name_score = self._score_exact_name(dest, destination_name, query)
        weighted_name = name_score * WEIGHT_EXACT_NAME
        breakdown["exact_name"] = round(weighted_name, 2)
        total += weighted_name

        # ----- 2. CATEGORY MATCH (weight: 30) -----
        cat_score = self._score_category(dest, category, query_tokens)
        weighted_cat = cat_score * WEIGHT_CATEGORY
        breakdown["category"] = round(weighted_cat, 2)
        total += weighted_cat

        # ----- 3. KEYWORD OVERLAP (weight: 20) -----
        kw_score = self._score_keywords(dest, query_tokens)
        weighted_kw = kw_score * WEIGHT_KEYWORD
        breakdown["keyword"] = round(weighted_kw, 2)
        total += weighted_kw

        # ----- 4. FUZZY TEXT MATCH (weight: 10) -----
        fuzzy_score = self._score_fuzzy(dest, query)
        weighted_fuzzy = fuzzy_score * WEIGHT_FUZZY
        breakdown["fuzzy"] = round(weighted_fuzzy, 2)
        total += weighted_fuzzy

        # ----- BUILDING BOOST / PENALTY -----
        if building:
            if dest.get("building", "").lower() == building.lower():
                total += 5.0  # bonus for matching building
                breakdown["building_bonus"] = 5.0
            # No penalty — building is a preference, not a hard filter

        return total, breakdown

    # ------------------------------------------------------------------
    # Individual scoring functions (each returns 0.0 to 1.0)
    # ------------------------------------------------------------------

    def _score_exact_name(
        self,
        dest: dict,
        destination_name: Optional[str],
        query: str,
    ) -> float:
        """
        Score based on exact or partial name/alias match.
        Returns 1.0 for exact match, partial score for substring match.
        """
        if not destination_name and not query:
            return 0.0

        dest_name_lower = dest["name"].lower()
        aliases_lower = [a.lower() for a in dest.get("aliases", [])]
        all_names = [dest_name_lower] + aliases_lower

        # Check against NLP-extracted destination name
        if destination_name:
            target = destination_name.lower().strip()
            for name in all_names:
                if target == name:
                    return 1.0  # Perfect match
                if target in name or name in target:
                    return 0.8  # Substring match

        # Check against raw query
        if query:
            query_lower = query.lower()
            for name in all_names:
                if name in query_lower:
                    return 0.7  # Name found in query
                # Check individual words of destination name
                name_words = name.split()
                if len(name_words) > 1:
                    matches = sum(1 for w in name_words if w in query_lower)
                    if matches > 0:
                        return 0.4 * (matches / len(name_words))

        return 0.0

    def _score_category(
        self,
        dest: dict,
        category: Optional[str],
        query_tokens: set[str],
    ) -> float:
        """
        Score based on category match.
        Returns 1.0 for exact category match, partial for related matches.
        """
        dest_category = dest.get("category", "").lower()

        if not dest_category:
            return 0.0

        # Direct category match from NLP extraction
        if category:
            cat_lower = category.lower().strip()
            if cat_lower == dest_category:
                return 1.0
            # Partial / related category matching
            if cat_lower in dest_category or dest_category in cat_lower:
                return 0.7

        # Fallback: check if category appears in query tokens
        cat_words = set(dest_category.replace("_", " ").split())
        if cat_words & query_tokens:
            return 0.5

        # Check purposes against query tokens
        purposes = {p.lower() for p in dest.get("purposes", [])}
        purpose_words = set()
        for p in purposes:
            purpose_words.update(p.split())

        overlap = query_tokens & purpose_words
        if overlap:
            return min(0.6, 0.2 * len(overlap))

        return 0.0

    def _score_keywords(self, dest: dict, query_tokens: set[str]) -> float:
        """
        Score based on keyword overlap between user query and destination
        keywords + purposes.
        Returns ratio of matching keywords (0.0 to 1.0).
        """
        if not query_tokens:
            return 0.0

        # Combine destination keywords and purpose words
        dest_keywords = {kw.lower() for kw in dest.get("keywords", [])}
        for purpose in dest.get("purposes", []):
            dest_keywords.update(purpose.lower().split())

        if not dest_keywords:
            return 0.0

        # Count how many query tokens match destination keywords
        matches = query_tokens & dest_keywords
        if not matches:
            return 0.0

        # Score = proportion of query tokens that matched, capped at 1.0
        # Also factor in how many dest keywords were hit
        query_ratio = len(matches) / len(query_tokens)
        dest_ratio = len(matches) / len(dest_keywords)

        return min(1.0, (query_ratio * 0.7 + dest_ratio * 0.3))

    def _score_fuzzy(self, dest: dict, query: str) -> float:
        """
        Fuzzy text similarity using SequenceMatcher.
        Compares query against destination name, description, and aliases.
        Returns best similarity ratio (0.0 to 1.0).
        """
        if not query:
            return 0.0

        query_lower = query.lower()
        candidates = [
            dest["name"].lower(),
            dest.get("description", "").lower(),
        ]
        candidates.extend(a.lower() for a in dest.get("aliases", []))

        best = 0.0
        for candidate in candidates:
            if not candidate:
                continue
            ratio = SequenceMatcher(None, query_lower, candidate).ratio()
            best = max(best, ratio)

        return best

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """
        Tokenize a text string into a set of lowercase words,
        filtering out stop words and very short tokens.
        """
        if not text:
            return set()

        # Common stop words to ignore
        stop_words = {
            "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
            "they", "them", "the", "a", "an", "is", "are", "was", "were",
            "be", "been", "am", "do", "does", "did", "has", "have", "had",
            "will", "would", "shall", "should", "can", "could", "may",
            "might", "must", "need", "to", "of", "in", "on", "at", "for",
            "with", "by", "from", "up", "about", "into", "through",
            "and", "but", "or", "so", "if", "not", "no", "this", "that",
            "what", "where", "when", "how", "which", "who", "there",
            "here", "some", "any", "all", "most", "please", "want",
            "looking", "find", "go", "get", "like", "recommend", "suggest",
        }

        words = text.lower().split()
        # Strip punctuation from each word
        cleaned = set()
        for w in words:
            clean = "".join(c for c in w if c.isalnum())
            if clean and len(clean) > 1 and clean not in stop_words:
                cleaned.add(clean)

        return cleaned

    @staticmethod
    def _empty_result(
        query: str,
        category: Optional[str],
        destination: Optional[str],
        building: Optional[str],
        reason: str = "",
    ) -> dict:
        """Return an empty recommendation result."""
        return {
            "recommendations": [],
            "top_match": None,
            "total_found": 0,
            "query_info": {
                "query": query,
                "category": category,
                "destination": destination,
                "building": building,
            },
            "message": reason or "No matching destinations found.",
        }
