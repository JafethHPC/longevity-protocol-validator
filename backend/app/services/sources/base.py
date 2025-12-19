"""
Base types and interfaces for data sources.
"""
from typing import TypedDict, Optional


class Paper(TypedDict):
    """Standard paper format used across all sources."""
    title: str
    abstract: str
    journal: str
    year: int
    pmid: str
    source: str  # Which source it came from (PubMed, OpenAlex, etc.)
    is_review: bool
    citation_count: int
    url: str
    # Added during processing
    relevance_score: Optional[float]
    relevance_reason: Optional[str]
