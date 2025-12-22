import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import research_router, papers_router, feedback_router, portfolio_router

app = FastAPI(title="Stock Research API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(research_router.router, prefix="/api", tags=["research"])
app.include_router(papers_router.router, prefix="/api", tags=["papers"])
app.include_router(feedback_router.router, prefix="/api", tags=["feedback"])
app.include_router(portfolio_router.router, prefix="/api", tags=["portfolio"])


@app.get("/api")
async def root():
    return {"status": "running", "message": "Stock Research API"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}

