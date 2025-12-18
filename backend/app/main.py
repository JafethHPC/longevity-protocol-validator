"""
FastAPI Application Entry Point

Research Report Generator API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.reports import router as reports_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered scientific literature analysis and report generation",
    version="3.0.0"
)

# Include API routers
app.include_router(reports_router)

# Static files for PDFs/figures
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS configuration
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
        "endpoints": {
            "generate_report": "/api/reports/generate",
            "get_report": "/api/reports/{report_id}",
            "follow_up": "/api/reports/{report_id}/followup"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)