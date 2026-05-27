import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.cache.redis_client import close_redis
from app.db.database import dispose_engine, get_engine
from app.limiter import limiter
from app.routers import feedback_router, papers_router, portfolio_router, research_router
from app.telemetry.langfuse_client import init_langfuse, shutdown_langfuse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_langfuse()
    try:
        get_engine()
        logger.info("SQLAlchemy async engine ready")
    except Exception as e:
        logger.warning("DB engine init deferred (set DATABASE_URL): %s", e)
    yield
    await dispose_engine()
    await close_redis()
    await shutdown_langfuse()


app = FastAPI(title="Stock Research API", version="2.0.0", lifespan=lifespan)
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "output", "reports")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

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
