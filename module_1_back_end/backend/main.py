from fastapi import FastAPI
from backend.api.v1.router import api_router

app = FastAPI(title="Module 1 Backend", version="0.0.0")
app.include_router(api_router, prefix="/api/v1")
