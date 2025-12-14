from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import List
from app.core.config import settings
from app.core.db import get_weaviate_client
from flashrank import Ranker, RerankRequest

class ResearchIngestion(BaseModel):
    """
    Structured response for scientific papers
    """
    answer_summary: str = Field(..., description="A direct, 2-3 sentence answer to the user's question")
    consensus_points: List[str] = Field(..., description="List of facts that appear to be agreed upon across multiple papers.")
    conflict_points: List[str] = Field(..., description="List of points where papers disagree or where results are inconclusive/contradictory.")
    limitations: str = Field(..., description="A note on what is NOT known or if the papers focus on specific groups (e.g., transplant patients, mice, etc.)")
    
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=settings.OPENAI_API_KEY
).with_structured_output(ResearchIngestion)

template = """You are an expert Biologist and Longevity Researcher.
Analyze the provided context papers to answer the user's question.

Your goal is to identify:
1. What do the papers agree on? (Consensus)
2. Where do they disagree or show mixed results? (Conflict)
3. What are the limitations? (e.g., "mouse only", "small sample size", "short study duration", etc.)

Context: {context}

Question: {question}

Answer: """

prompt = ChatPromptTemplate.from_template(template)
ranker = Ranker() 

def get_context(query:str):
    """
    Retrieves the raw text chunks from Weaviate to feed into the AI.
    Uses Two-Stage Retrieval:
    1. Vector Search (Broad): Fetch top 50 chunks
    2. Reranking (precise): Filter for top 10 chunks using Cross-Encoder
    """
    client = get_weaviate_client()

    try:
        papers = client.collections.get("Paper")
        response = papers.query.near_text(
            query=query,
            limit=50
        )
        
        if not response.objects:
            return ""

        passages = []
        for idx, obj in enumerate(response.objects):
            passages.append({
                "id": idx,
                "text": obj.properties.get('abstract', ''),
                "meta": obj.properties
            })

        rerank_request = RerankRequest(query=query, passages=passages)
        reranked_results = ranker.rerank(rerank_request)
        
        top_results = reranked_results[:10]

        context_str = "\n\n".join([
            f"Paper: {res['meta']['title']}\nSource: {res['meta']['source_id']}\nAbstract: {res['text']}"
            for res in top_results
        ])
        
        return context_str
    
    except Exception as e:
        print(f"Error getting context: {e}")
        return ""

    finally: 
        client.close()

def generate_answer(query: str):
    """
    Generates an answer to the user's question based on the context.

    The full RAG Chain:
    1. Get Context (Weaviate)
    2. Format Prompt
    3. Send to GPT-4o
    """
    context_text = get_context(query)

    chain = prompt | llm
    structured_response = chain.invoke(
        {
            "context": context_text,
            "question": query
        }
    )

    return {
        "answer": structured_response.answer_summary,
        "consensus": structured_response.consensus_points,
        "conflict": structured_response.conflict_points,
        "limitations": structured_response.limitations,
        "context_used": context_text
    }
    