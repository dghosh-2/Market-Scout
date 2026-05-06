import os
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.routers import research_router, papers_router, feedback_router, portfolio_router
from app.limiter import limiter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.db import smoldb

        smoldb.init_schema()
        logger.info("smoldb schema initialized")
    except Exception as e:
        logger.warning("smoldb init skipped or failed (set SMOLDB_KEY): %s", e)
    yield


app = FastAPI(title="Stock Research API", version="1.0.0", lifespan=lifespan)

app.state.limiter = limiter


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": getattr(exc, "detail", "Rate limit exceeded")},
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://market-scout-chi.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "output", "reports")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Ensure directories exist
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Mount static files for reports
app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

# Include routers
app.include_router(research_router.router, prefix="/api", tags=["research"])
app.include_router(papers_router.router, prefix="/api", tags=["papers"])
app.include_router(feedback_router.router, prefix="/api", tags=["feedback"])
app.include_router(portfolio_router.router, prefix="/api", tags=["portfolio"])


@app.get("/")
async def root():
    return {"status": "running", "message": "Stock Research API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
