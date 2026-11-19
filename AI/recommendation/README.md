# AI Recommendation Module (Module 2)

This directory contains the AI Recommendation Engine built by **Member 2**.

## Structure
```
AI/recommendation/
├── __init__.py                  # Package init, exports RecommendationEngine
├── recommendation_engine.py     # Core scoring algorithm
├── knowledge_base.py            # Location data loader + repository
├── data/
│   └── locations.json           # Destination data (editable)
└── tests/
    └── test_recommendation.py   # 10 test cases
```

## How to test
```bash
cd Workshop-2
python -m AI.recommendation.tests.test_recommendation
```

## How Member 4 integrates this
```python
from AI.recommendation import RecommendationEngine

engine = RecommendationEngine()
result = engine.recommend(
    query="I need to print my assignment",
    category="printing",
)
print(result["top_match"])
```
