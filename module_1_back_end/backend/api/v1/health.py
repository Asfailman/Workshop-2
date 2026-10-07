from fastapi import APIRouter

#test the server is running 
router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}
