"""
Retrieval Schemas

Pydantic models for the retrieval pipeline (query optimization, relevance filtering).
"""
from pydantic import BaseModel, Field
from typing import List


class OptimizedQueries(BaseModel):
    """Structured output for query optimization"""
    pubmed_query: str = Field(description="Optimized query for PubMed with MeSH terms and boolean operators")
    semantic_query: str = Field(description="Natural language query optimized for semantic search")
    key_concepts: List[str] = Field(description="Key scientific concepts from the query")


class PaperRelevance(BaseModel):
    """Relevance assessment for a single paper"""
    is_relevant: bool = Field(description="Whether this paper is relevant to answering the question")
    reason: str = Field(description="Brief reason for the relevance decision")
