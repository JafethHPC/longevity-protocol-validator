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
    source: str
    is_review: bool
    citation_count: int
    url: str
    relevance_score: Optional[float]
    relevance_reason: Optional[str]
