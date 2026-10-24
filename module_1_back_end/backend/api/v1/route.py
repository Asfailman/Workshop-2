from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.routing_service import RoutingService

router = APIRouter()

# Initialize the service (loads the JSON map into memory on startup)
routing_service = RoutingService()

class RouteRequest(BaseModel):
    start_id: str
    destination_id: str

@router.post("/")
async def calculate_route(request: RouteRequest):
    """
    Calculate the shortest indoor route between two points.
    Example body:
    {
      "start_id": "MAIN_ENTRANCE",
      "destination_id": "B_B_L2_AI_LAB_1"
    }
    """
    result = routing_service.get_shortest_route(request.start_id, request.destination_id)
    
    # If the service returns an error dict, raise a 400 Bad Request
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return result