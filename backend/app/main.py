import uuid
import json
import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
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

@app.get("/chat/stream")
async def chat_stream(
    query: str = Query(..., description="The user's question"),
    thread_id: Optional[str] = Query(None, description="Thread ID for conversation continuity")
):
    """
    Streaming Research Agent Chat Endpoint using Server-Sent Events (SSE).
    """
    thread_id = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    config["recursion_limit"] = 50

    async def event_generator():
        try:
            yield f"event: status\ndata: {json.dumps({'step': 'starting', 'message': 'Starting research agent...'})}\n\n"
            await asyncio.sleep(0.01)

            current_state = agent_executor.get_state(config)
            protocols_before = len(current_state.values.get("protocols", [])) if current_state.values else 0

            final_answer = ""
            current_node = ""

            for event in agent_executor.stream(
                {"messages": [HumanMessage(content=query)]},
                config=config,
                stream_mode="updates"
            ):
                for node_name, node_output in event.items():
                    if node_name != current_node:
                        current_node = node_name
                        status_msg = {
                            "agent": "Agent is reasoning...",
                            "tools": "Executing research tools...",
                            "grader": "Grading document relevance...",
                            "rewrite": "Refining search query...",
                            "answer_gen": "Generating final answer..."
                        }.get(node_name, f"Processing {node_name}...")
                        
                        yield f"event: status\ndata: {json.dumps({'step': node_name, 'message': status_msg})}\n\n"
                        await asyncio.sleep(0.01)

                    if node_name == "answer_gen" and "messages" in node_output:
                        for msg in node_output["messages"]:
                            if hasattr(msg, "content") and msg.content:
                                final_answer = msg.content
                                yield f"event: token\ndata: {json.dumps({'text': msg.content})}\n\n"
                                await asyncio.sleep(0.01)

                    if "protocols" in node_output and node_output["protocols"]:
                        new_protocols = node_output["protocols"]
                        yield f"event: protocols\ndata: {json.dumps({'protocols': new_protocols})}\n\n"
                        await asyncio.sleep(0.01)

            yield f"event: complete\ndata: {json.dumps({'thread_id': thread_id})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)