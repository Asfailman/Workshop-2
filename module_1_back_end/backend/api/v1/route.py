from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_route():
    return {"message": "Route endpoint - not implemented yet"}
