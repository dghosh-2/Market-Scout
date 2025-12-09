import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import research_router, papers_router, feedback_router, portfolio_router

app = FastAPI(title="Stock Research API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
