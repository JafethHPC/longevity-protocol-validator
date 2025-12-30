"""
Base types and interfaces for data sources.

This module defines the standard paper format and abstract base class
that all data sources should implement for consistency.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field


class Paper(BaseModel):
    """
    Standard paper format used across all sources.
    
    Using Pydantic validates all paper data automatically and provides
    consistent types. All source implementations should return papers
    matching this schema.
    """
    title: str
    abstract: str
    journal: str = ""
    year: int = 0
    pmid: str = ""
    doi: str = ""
    source: str  # Name of the data source (e.g., "PubMed", "OpenAlex")
    is_review: bool = False
    citation_count: int = 0
    url: str = ""
    
    # Type discriminator: "paper" or "clinical_trial"
    type: str = Field(default="paper")
    
    # Optional fields for clinical trials
    status: Optional[str] = None
    phase: Optional[str] = None
    has_results: Optional[bool] = None
    conditions: Optional[List[str]] = None
    interventions: Optional[List[str]] = None
    
    # Relevance metadata (populated during ranking)
    relevance_score: Optional[float] = None
    relevance_reason: Optional[str] = None


class BaseSource(ABC):
    """
    Abstract base class for all data sources.
    
    Implementing this interface ensures all sources have a consistent API.
    All search methods should be async for parallel fetching.
    
    To add a new source:
    1. Create a class that inherits from BaseSource
    2. Implement the name property and search method
    3. Register it in the sources __init__.py
    4. Add it to the retrieval pipeline
    
    Example:
        class NewSource(BaseSource):
            @property
            def name(self) -> str:
                return "NewSource"
            
            async def search(self, query: str, max_results: int = 50) -> List[Paper]:
                # Implementation here
                pass
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the data source."""
        pass
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 50) -> List[Paper]:
        """
        Search this source for papers matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Paper objects matching the query
        """
        pass

