from fastapi import APIRouter
from . import health, assistant, destinations

# Create a router for the API
api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["Assistant"])
api_router.include_router(destinations.router, prefix="/destinations", tags=["Destinations"])

