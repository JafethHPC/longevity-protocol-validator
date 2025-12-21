"""
Data sources for scientific paper retrieval.

Each source is implemented in its own module for maintainability.
All search functions are async for parallel execution.

To add a new source:
1. Create a new file (e.g., new_source.py)
2. Implement async search_new_source(query, max_results) -> List[Dict]
3. Export it here
4. Add it to the retrieval pipeline in retrieval.py
"""
from .pubmed import search_pubmed
from .openalex import search_openalex
from .europe_pmc import search_europe_pmc
from .crossref import search_crossref
from .base import Paper

__all__ = [
    "search_pubmed",
    "search_openalex",
    "search_europe_pmc",
    "search_crossref",
    "Paper",
]
