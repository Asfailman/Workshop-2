from fastapi import APIRouter, HTTPException
from backend.services.destination_service import DestinationService

router = APIRouter()
destination_service = DestinationService()

@router.get("/")
async def list_destinations(query: str = ""):
    return destination_service.search(query)

@router.get("/{destination_id}")
async def get_destination(destination_id: str):
    destination = destination_service.get_by_id(destination_id)
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    return destination