from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    query: Optional[str] = Field(default="", description="Natural-language query for destination search")
    category: Optional[str] = Field(default=None, description="Category filter (e.g. laboratory, lecture_hall)")
    destination: Optional[str] = Field(default=None, description="Destination name or alias hint")
    building: Optional[str] = Field(default=None, description="Building constraint (e.g. Block A, Block B)")


class DestinationRecommendationItem(BaseModel):
    destination_id: str = Field(..., description="Unique destination ID matching campus_map.json")
    name: str = Field(..., description="Name of destination")
    category: Optional[str] = Field("", description="Category")
    building: Optional[str] = Field("", description="Building / Block")
    floor: Optional[Any] = Field("", description="Floor level")
    room_number: Optional[str] = Field(None, description="Room number if any")
    description: Optional[str] = Field("", description="Description")
    opening_hours: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Opening hours")
    score: float = Field(..., description="Recommendation score (0-100)")
    score_breakdown: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Score component breakdown")


class RecommendResponse(BaseModel):
    recommendations: List[DestinationRecommendationItem] = Field(default_factory=list, description="Ranked recommendations")
    top_match: Optional[DestinationRecommendationItem] = Field(None, description="Best matching destination")
    total_found: int = Field(0, description="Total candidates matching criteria")
    query_info: Dict[str, Any] = Field(default_factory=dict, description="Query parameters used")
