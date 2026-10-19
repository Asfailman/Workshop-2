"""
Module 2 - Recommendation Engine Tests
=======================================
Tests for the AI recommendation scoring algorithm.

Run from project root:
    python -m AI.recommendation.tests.test_recommendation
"""

import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from AI.recommendation import RecommendationEngine


def get_engine():
    """Create a fresh engine instance for testing."""
    return RecommendationEngine()


# ---------------------------------------------------------------------------
# Test 1: Exact destination name match
# ---------------------------------------------------------------------------
def test_exact_destination_match():
    """When the user asks for 'Main Library', it should rank first."""
    engine = get_engine()
    result = engine.recommend(
        query="Where is the Main Library?",
        destination="Main Library",
    )
    assert result["top_match"] is not None
    assert result["top_match"]["name"] == "Main Library"
    assert result["top_match"]["score"] > 50
    print(f"[PASS] Exact match: {result['top_match']['name']} "
          f"(score: {result['top_match']['score']})")


# ---------------------------------------------------------------------------
# Test 2: Category-based recommendation (printing)
# ---------------------------------------------------------------------------
def test_category_printing():
    """User asks for printing -> Printing Room should rank top."""
    engine = get_engine()
    result = engine.recommend(
        query="I need to print my assignment",
        category="printing",
    )
    assert result["top_match"] is not None
    assert result["top_match"]["name"] == "Printing Room"
    print(f"[PASS] Category match (printing): {result['top_match']['name']} "
          f"(score: {result['top_match']['score']})")


# ---------------------------------------------------------------------------
# Test 3: Category-based recommendation (food)
# ---------------------------------------------------------------------------
def test_category_food():
    """User asks for food -> Cafeteria should rank top."""
    engine = get_engine()
    result = engine.recommend(
        query="I'm hungry, where can I eat?",
        category="food",
    )
    assert result["top_match"] is not None
    assert result["top_match"]["name"] == "Cafeteria"
    print(f"[PASS] Category match (food): {result['top_match']['name']} "
          f"(score: {result['top_match']['score']})")


# ---------------------------------------------------------------------------
# Test 4: Keyword-based recommendation (study)
# ---------------------------------------------------------------------------
def test_keyword_study():
    """User asks for a quiet study place -> study-related destinations."""
    engine = get_engine()
    result = engine.recommend(
        query="Can you recommend a quiet place to study?",
        category="study area",
    )
    assert result["top_match"] is not None
    assert result["top_match"]["name"] in ["Study Room A", "Main Library"]
    print(f"[PASS] Keyword match (study): {result['top_match']['name']} "
          f"(score: {result['top_match']['score']})")


# ---------------------------------------------------------------------------
# Test 5: Building constraint
# ---------------------------------------------------------------------------
def test_building_filter():
    """Building constraint should boost matching destinations."""
    engine = get_engine()
    result = engine.recommend(
        query="Where can I study?",
        category="study area",
        building="Block A",
    )
    assert result["top_match"] is not None
    top = result["top_match"]
    assert top["building"] == "Block A"
    print(f"[PASS] Building filter: {top['name']} in {top['building']} "
          f"(score: {top['score']})")


# ---------------------------------------------------------------------------
# Test 6: Alias match
# ---------------------------------------------------------------------------
def test_alias_match():
    """User uses alias 'toilet' -> should find restroom."""
    engine = get_engine()
    result = engine.recommend(
        query="Where is the toilet?",
        destination="toilet",
    )
    assert result["top_match"] is not None
    assert "restroom" in result["top_match"]["name"].lower() or \
           "toilet" in result["top_match"]["name"].lower() or \
           result["top_match"]["category"] == "restroom"
    print(f"[PASS] Alias match (toilet): {result['top_match']['name']} "
          f"(score: {result['top_match']['score']})")


# ---------------------------------------------------------------------------
# Test 7: Alternative recommendations are returned
# ---------------------------------------------------------------------------
def test_alternatives_returned():
    """Multiple recommendations should be returned for broad queries."""
    engine = get_engine()
    result = engine.recommend(
        query="I need a computer lab or study room",
    )
    assert len(result["recommendations"]) >= 2
    print(f"[PASS] Alternatives: {len(result['recommendations'])} recommendations returned")
    for rec in result["recommendations"]:
        print(f"   - {rec['name']} (score: {rec['score']})")


# ---------------------------------------------------------------------------
# Test 8: No results for nonsense query
# ---------------------------------------------------------------------------
def test_no_match_nonsense():
    """Completely irrelevant query should return no/few matches."""
    engine = get_engine()
    result = engine.recommend(
        query="xyzzy foobar baz",
    )
    if result["top_match"]:
        assert result["top_match"]["score"] < 20
    print(f"[PASS] Nonsense query: {result['total_found']} results "
          f"(top score: {result['top_match']['score'] if result['top_match'] else 0})")


# ---------------------------------------------------------------------------
# Test 9: End-to-end scenario - "I need to print my assignment"
# ---------------------------------------------------------------------------
def test_e2e_print_assignment():
    """
    End-to-end test matching the project checklist scenario:
    User says "I need to print my assignment" -> Printing Room is recommended.
    """
    engine = get_engine()
    result = engine.recommend(
        query="I need to print my assignment",
        category="printing",
        destination=None,
        building=None,
    )
    assert result["top_match"] is not None
    assert result["top_match"]["destination_id"] == "DEST_002"
    assert result["top_match"]["name"] == "Printing Room"
    print(f"[PASS] E2E (print assignment): {result['top_match']['name']} "
          f"at {result['top_match']['building']}, {result['top_match']['floor']} "
          f"(score: {result['top_match']['score']})")
    print(f"   Score breakdown: {result['top_match']['score_breakdown']}")


# ---------------------------------------------------------------------------
# Test 10: Score breakdown is populated
# ---------------------------------------------------------------------------
def test_score_breakdown():
    """Verify that score breakdown contains all expected components."""
    engine = get_engine()
    result = engine.recommend(
        query="Where is the library?",
        destination="Library",
        category="library",
    )
    assert result["top_match"] is not None
    breakdown = result["top_match"]["score_breakdown"]
    assert "exact_name" in breakdown
    assert "category" in breakdown
    assert "keyword" in breakdown
    assert "fuzzy" in breakdown
    print(f"[PASS] Score breakdown: {breakdown}")


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        test_exact_destination_match,
        test_category_printing,
        test_category_food,
        test_keyword_study,
        test_building_filter,
        test_alias_match,
        test_alternatives_returned,
        test_no_match_nonsense,
        test_e2e_print_assignment,
        test_score_breakdown,
    ]

    print("=" * 60)
    print("Module 2 - Recommendation Engine Tests")
    print("=" * 60)

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)
