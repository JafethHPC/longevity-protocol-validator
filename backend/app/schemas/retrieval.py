"""
Retrieval Schemas

Pydantic models for the retrieval pipeline (query optimization, relevance filtering).
"""
from pydantic import BaseModel, Field
from typing import List


class OptimizedQueries(BaseModel):
    """Structured output for query optimization"""
    pubmed_query: str = Field(description="Optimized query for PubMed with MeSH terms, synonyms, and boolean operators")
    semantic_query: str = Field(description="Natural language query with mechanisms, biomarkers, and related terms for semantic search")
    key_concepts: List[str] = Field(description="5-8 key scientific concepts including main topic, mechanisms, biomarkers, and related terms")


class PaperRelevance(BaseModel):
    """Relevance assessment for a single paper"""
    is_relevant: bool = Field(description="Whether this paper is relevant to answering the question")
    reason: str = Field(description="Brief reason for the relevance decision")


class PaperEvaluation(BaseModel):
    """Evaluation result for a single paper in a batch"""
    paper_number: int = Field(description="The paper number (1-indexed) being evaluated")
    is_relevant: bool = Field(description="Whether this paper is relevant to answering the question")
    reason: str = Field(description="Brief reason for the relevance decision (max 50 words)")


class BatchPaperRelevance(BaseModel):
    """Batch relevance assessment for multiple papers"""
    evaluations: List[PaperEvaluation] = Field(
        description="List of relevance evaluations, one for each paper in the batch"
    )
