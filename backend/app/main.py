import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from app.core.config import settings
from langsmith import Client
from app.rag import generate_answer
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

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    consensus: list[str]
    conflict: list[str]
    limitations: str
    context_used: str

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

@app.post("/chat", response_model=ChatResponse)
async def chat_with_papers(request: ChatRequest):
    """
    RAG Chat endpoint: Generates an answer based on stored papers.
    """
    try: 
        result = generate_answer(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/agent/research")
async def agent_research(request: AgentRequest):
    """
    Trigger the Autonomous Researcher
    """
    try:
        thread_id = request.thread_id or str(uuid.uuid4())

        config = {"configurable": {"thread_id": thread_id}}

        final_state = agent_executor.invoke(
            {"messages": [HumanMessage(content=request.query)]},
            config=config
        )

        final_response = final_state["messages"][-1].content
        protocols = final_state.get("protocols", [])

        return {
            "result": final_response, 
            "protocols": protocols,
            "thread_id": thread_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)