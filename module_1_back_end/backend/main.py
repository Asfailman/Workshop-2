import sys
from pathlib import Path

# Ensure module_1_back_end and repository root are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

for p in [str(BASE_DIR), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1.router import api_router

app = FastAPI(title="Module 1 Backend", version="0.0.1")

# Enable CORS for frontend / Android connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    """Automatically redirect root visitors to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")

app.include_router(api_router, prefix="/api/v1")



