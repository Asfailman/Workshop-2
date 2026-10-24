"""
AI Recommendation Module (Module 2)
====================================
Self-contained AI recommendation engine for destination ranking.

Usage:
    from AI.recommendation import RecommendationEngine

    engine = RecommendationEngine()
    result = engine.recommend(query="I need to print", category="printing")
"""

from .recommendation_engine import RecommendationEngine
from .knowledge_base import KnowledgeBase

__all__ = ["RecommendationEngine", "KnowledgeBase"]
