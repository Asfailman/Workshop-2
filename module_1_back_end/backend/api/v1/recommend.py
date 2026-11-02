"""
Recommend API Endpoint
======================
Exposes the AI Recommendation Engine for finding and ranking destinations.
"""

from typing import Optional
from fastapi import APIRouter, Query
from backend.schemas.recommendation import RecommendRequest, RecommendResponse

# Import RecommendationEngine from AI package
try:
    from AI.recommendation import RecommendationEngine
except ImportError:
    try:
        from recommendation import RecommendationEngine
    except ImportError:
        RecommendationEngine = None

router = APIRouter()
_engine = None


def get_engine():
    global _engine
    if _engine is None and RecommendationEngine is not None:
        _engine = RecommendationEngine()
    return _engine


@router.post("/", response_model=RecommendResponse)
async def post_recommendations(request: RecommendRequest):
    """
    Generate ranked destination recommendations using the AI Recommendation Engine.
    """
    engine = get_engine()
    if engine is None:
        return RecommendResponse(
            recommendations=[],
            top_match=None,
            total_found=0,
            query_info={"error": "RecommendationEngine unavailable"},
        )

    result = engine.recommend(
        query=request.query or "",
        category=request.category,
        destination=request.destination,
        building=request.building,
    )
    return result


@router.get("/", response_model=RecommendResponse)
async def get_recommendations(
    query: str = Query(default="", description="Search query"),
    category: Optional[str] = Query(default=None, description="Category filter"),
    destination: Optional[str] = Query(default=None, description="Destination hint"),
    building: Optional[str] = Query(default=None, description="Building constraint"),
):
    """
    GET endpoint for destination recommendations via query parameters.
    """
    engine = get_engine()
    if engine is None:
        return RecommendResponse(
            recommendations=[],
            top_match=None,
            total_found=0,
            query_info={"error": "RecommendationEngine unavailable"},
        )

    result = engine.recommend(
        query=query,
        category=category,
        destination=destination,
        building=building,
    )
    return result
