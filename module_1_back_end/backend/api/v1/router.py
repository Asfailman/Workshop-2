from fastapi import APIRouter
from . import health, route, assistant, destinations, recommend

# create a router for the API
api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(route.router, prefix="/route", tags=["Route"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["Assistant"])
api_router.include_router(destinations.router, prefix="/destinations", tags=["Destinations"])
api_router.include_router(recommend.router, prefix="/recommend", tags=["Recommend"])
