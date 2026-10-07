from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/query")
async def assistant_query(payload: dict):
    # API HASNT BEEN IMPLEMENTED YET, THIS IS JUST A PLACEHOLDER
    raise HTTPException(status_code=501, detail="Not implemented")