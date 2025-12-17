import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from app.core.config import settings
from app.core.db import get_weaviate_client
from langchain_core.messages import HumanMessage
from app.agent import agent_executor

app = FastAPI(title=settings.PROJECT_NAME)

app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "http://localhost:4200",
    "http://localhost:8081",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class SearchRequest(BaseModel):
    query: str
    limit: int = 3

class PaperResponse(BaseModel):
    title: str
    abstract: str
    years: int
    distance: float

class AgentRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None

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
    client = get_weaviate_client()

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

@app.post("/chat")
async def chat_endpoint(request: AgentRequest):
    """
    Unified Research Agent Chat Endpoint.
    Replaces old simple RAG chat.
    """
    try:
        thread_id = request.thread_id or str(uuid.uuid4())

        config = {"configurable": {"thread_id": thread_id}}
        config["recursion_limit"] = 50

        # Get the current state to know how many protocols exist BEFORE this turn
        current_state = agent_executor.get_state(config)
        protocols_before = len(current_state.values.get("protocols", [])) if current_state.values else 0

        final_state = agent_executor.invoke(
            {"messages": [HumanMessage(content=request.query)]},
            config=config
        )

        final_response = final_state["messages"][-1].content
        all_protocols = final_state.get("protocols", [])
        
        # Only return the NEW protocols added in THIS turn
        current_turn_protocols = all_protocols[protocols_before:]

        return {
            "answer": final_response, 
            "protocols": current_turn_protocols,
            "thread_id": thread_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)