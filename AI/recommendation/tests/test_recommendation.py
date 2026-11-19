"""
Module 2 - Recommendation Engine Tests
=======================================
Tests for the AI recommendation scoring algorithm using backend campus location data.

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
    """When the user asks for 'AI Lab 1', it should rank first."""
    engine = get_engine()
    result = engine.recommend(
        query="Where is the AI Lab 1?",
        destination="AI Lab 1",
    )
    assert result["top_match"] is not None
    assert result["top_match"]["destination_id"] == "B_B_L2_AI_LAB_1"
    assert result["top_match"]["score"] > 50
    print(f"[PASS] Exact match: {result['top_match']['name']} "
          f"(score: {result['top_match']['score']})")


# ---------------------------------------------------------------------------
# Test 2: Category-based recommendation (laboratory)
# ---------------------------------------------------------------------------
def test_category_laboratory():
    """User asks for laboratory -> Lab destinations should rank top."""
    engine = get_engine()
    result = engine.recommend(
        query="I need to go to a computer lab for programming",
        category="laboratory",
    )
    assert result["top_match"] is not None
    assert result["top_match"]["category"] == "laboratory"
    print(f"[PASS] Category match (laboratory): {result['top_match']['name']} "
          f"(score: {result['top_match']['score']})")


# ---------------------------------------------------------------------------
# Test 3: Category-based recommendation (lecture_hall)
# ---------------------------------------------------------------------------
def test_category_lecture_hall():
    """User asks for presentation / lecture hall -> Mini Theatre should rank top."""
    engine = get_engine()
    result = engine.recommend(
        query="Where is the lecture theatre for the talk?",
        category="lecture_hall",
    )
    assert result["top_match"] is not None
    assert result["top_match"]["destination_id"] == "B_D_L3_MINI_THEATRE"
    print(f"[PASS] Category match (lecture_hall): {result['top_match']['name']} "
          f"(score: {result['top_match']['score']})")


# ---------------------------------------------------------------------------
# Test 4: Keyword-based recommendation (robotics)
# ---------------------------------------------------------------------------
def test_keyword_robotics():
    """User asks for robotics/sensors -> Robotics Lab should rank top."""
    engine = get_engine()
    result = engine.recommend(
        query="Where can I work on arduino and robot sensors?",
    )
    assert result["top_match"] is not None
    assert result["top_match"]["destination_id"] == "B_B_L3_ROBOTICS_LAB"
    print(f"[PASS] Keyword match (robotics): {result['top_match']['name']} "
          f"(score: {result['top_match']['score']})")


# ---------------------------------------------------------------------------
# Test 5: Building constraint
# ---------------------------------------------------------------------------
def test_building_filter():
    """Building constraint should boost matching destinations."""
    engine = get_engine()
    result = engine.recommend(
        query="Where can I find an AI lab?",
        building="Block B",
    )
    assert result["top_match"] is not None
    top = result["top_match"]
    assert top["building"] == "Block B"
    print(f"[PASS] Building filter: {top['name']} in {top['building']} "
          f"(score: {top['score']})")


# ---------------------------------------------------------------------------
# Test 6: Alias match
# ---------------------------------------------------------------------------
def test_alias_match():
    """User uses alias 'Lobi' or 'Entrance' -> should find Main Entrance."""
    engine = get_engine()
    result = engine.recommend(
        query="Where is the lobby?",
        destination="Lobby",
    )
    assert result["top_match"] is not None
    assert result["top_match"]["destination_id"] == "MAIN_ENTRANCE"
    print(f"[PASS] Alias match (lobby): {result['top_match']['name']} "
          f"(score: {result['top_match']['score']})")


# ---------------------------------------------------------------------------
# Test 7: Alternative recommendations are returned
# ---------------------------------------------------------------------------
def test_alternatives_returned():
    """Multiple recommendations should be returned for broad queries."""
    engine = get_engine()
    result = engine.recommend(
        query="Where can I find a lab?",
        category="laboratory",
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
# Test 9: End-to-end scenario - "Where can I do machine learning research?"
# ---------------------------------------------------------------------------
def test_e2e_machine_learning():
    """
    End-to-end test matching real campus scenario:
    User asks for machine learning -> AI Lab 1 / 2 is recommended.
    """
    engine = get_engine()
    result = engine.recommend(
        query="Where can I do machine learning and deep learning coursework?",
        category="laboratory",
    )
    assert result["top_match"] is not None
    assert "AI_LAB" in result["top_match"]["destination_id"]
    print(f"[PASS] E2E (machine learning): {result['top_match']['name']} "
          f"at {result['top_match']['building']}, Floor {result['top_match']['floor']} "
          f"(score: {result['top_match']['score']})")
    print(f"   Score breakdown: {result['top_match']['score_breakdown']}")


# ---------------------------------------------------------------------------
# Test 10: Score breakdown is populated
# ---------------------------------------------------------------------------
def test_score_breakdown():
    """Verify that score breakdown contains all expected components."""
    engine = get_engine()
    result = engine.recommend(
        query="Where is the robotics lab?",
        destination="Robotics Lab",
        category="laboratory",
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
        test_category_laboratory,
        test_category_lecture_hall,
        test_keyword_robotics,
        test_building_filter,
        test_alias_match,
        test_alternatives_returned,
        test_no_match_nonsense,
        test_e2e_machine_learning,
        test_score_breakdown,
    ]

    print("=" * 60)
    print("Module 2 - Recommendation Engine Tests (Real Campus Data)")
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
