"""
Retrieval Schemas

Pydantic models for the retrieval pipeline (query optimization, relevance filtering).
"""
from pydantic import BaseModel, Field
from typing import List, Optional


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


class SourceConfig(BaseModel):
    """Configuration for a specific source type"""
    enabled: bool = Field(default=True, description="Whether this source is enabled")
    max_results: int = Field(default=100, ge=0, le=500, description="Maximum results to fetch from this source")


class ResearchConfig(BaseModel):
    """
    Configuration for the research retrieval pipeline.
    Controls which sources to use and how many results to fetch from each.
    """
    # Final output limits
    max_final_sources: int = Field(
        default=15, 
        ge=5, 
        le=50, 
        description="Maximum number of sources in the final report"
    )
    min_clinical_trials: int = Field(
        default=3, 
        ge=0, 
        le=10, 
        description="Minimum number of clinical trials to include (if available)"
    )
    min_papers: int = Field(
        default=5, 
        ge=0, 
        le=20, 
        description="Minimum number of research papers to include"
    )
    
    # Source-specific configurations
    pubmed: SourceConfig = Field(default_factory=lambda: SourceConfig(enabled=True, max_results=100))
    openalex: SourceConfig = Field(default_factory=lambda: SourceConfig(enabled=True, max_results=100))
    europe_pmc: SourceConfig = Field(default_factory=lambda: SourceConfig(enabled=True, max_results=100))
    crossref: SourceConfig = Field(default_factory=lambda: SourceConfig(enabled=True, max_results=100))
    clinical_trials: SourceConfig = Field(default_factory=lambda: SourceConfig(enabled=True, max_results=25))
    
    # Processing options
    include_fulltext: bool = Field(default=True, description="Whether to fetch full text for papers")
    clinical_trial_boost: float = Field(
        default=0.15, 
        ge=0.0, 
        le=0.5, 
        description="Relevance boost for clinical trials in ranking"
    )
    
    @classmethod
    def default(cls) -> "ResearchConfig":
        """Return the default configuration"""
        return cls()
