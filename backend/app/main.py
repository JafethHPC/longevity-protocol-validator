"""
FastAPI Application Entry Point

Research Report Generator API
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.api.reports import router as reports_router
from app.services.cache import report_cache

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered scientific literature analysis and report generation",
    version="3.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.include_router(reports_router)

# Mount static files only if directory exists
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "http://localhost:4200",
    "http://localhost:58766",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def health_check():
    """Root endpoint to verify the server is running."""
    return {
        "status": "active",
        "project": settings.PROJECT_NAME,
        "version": "3.0.0",
        "cache": {
            "type": "redis" if report_cache.is_connected else "in-memory",
            "connected": report_cache.is_connected
        },
        "rate_limiting": {
            "enabled": True,
            "storage": "redis" if report_cache.is_connected else "memory"
        },
        "endpoints": {
            "generate_report": "/api/reports/generate",
            "get_report": "/api/reports/{report_id}",
            "follow_up": "/api/reports/{report_id}/followup"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)