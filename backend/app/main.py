from fastapi import FastAPI
from app.core.config import settings
from langsmith import Client

app = FastAPI(title=settings.PROJECT_NAME)

client = Client()

@app.get("/")
async def health_check():
    """
    Root endpoint to verify the server is running and LangSmith env vars are loaded.
    """
    return {
        "status": "active",
        "project": settings.PROJECT_NAME,
        "langsmith_project": settings.LANGCHAIN_PROJECT,
        "docs_url": "http://localhost:8000/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)