from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import weaviate
import weaviate.classes.query as wvq
from app.core.config import settings
from langsmith import Client

app = FastAPI(title=settings.PROJECT_NAME)

class SearchRequest(BaseModel):
    query: str
    limit: int = 3

class PaperResponse(BaseModel):
    title: str
    abstract: str
    years: int
    distance: float

@app.get("/")
async def health_check():
    """
    Root endpoint to verify the server is running and LangSmith env vars are loaded.
    """
    return {
        "status": "active",
        "project": settings.PROJECT_NAME,
        "project_name": settings.LANGCHAIN_PROJECT,
    }

@app.post("/search")
async def search_papers(request: SearchRequest):
    """
    Semantic Search endpoint.
    Accepts a query string, embeds it, and finds the nearest papers in Weaviate.
    """
    client = weaviate.connect_to_local(
        headers={
            "X-OpenAI-Api-Key": settings.OPENAI_API_KEY
        }
    )

    try:
        papers = client.collections.get("Paper")

        response = papers.query.near_text(
            query=request.query,
            limit=request.limit,
            return_metadata=wvq.MetadataQuery(distance=True)
        )

        results = []
        for obj in response.objects:
            results.append(
                PaperResponse(
                    title=obj.properties["title"],
                    abstract=obj.properties["abstract"],
                    years=obj.properties["year"],
                    distance=obj.metadata.distance
                )
            )

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)