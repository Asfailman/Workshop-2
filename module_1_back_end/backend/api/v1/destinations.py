from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/")
async def list_destinations(query: str = ""):
    # API HASNT BEEN IMPLEMENTED YET, THIS IS JUST A PLACEHOLDER
    raise HTTPException(status_code=501, detail="Not implemented")