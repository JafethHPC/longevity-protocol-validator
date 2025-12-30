"""
Enhanced Multi-Source Retrieval System with Parallel Processing

This package provides paper retrieval functionality by:
1. Optimizing search queries for each source
2. Fetching from multiple sources (PubMed, OpenAlex, Europe PMC, CrossRef, ClinicalTrials.gov)
3. Ranking ALL papers by semantic similarity + citation count
4. Parallel batch LLM-based relevance filtering for speed
5. Full-text enrichment from open access sources

Package Structure:
- pipeline.py: Main enhanced_retrieval orchestration
- query_optimizer.py: Query optimization with LLM
- ranking.py: Semantic ranking and deduplication
- llm_filter.py: Parallel LLM-based filtering
- fulltext_enrichment.py: Full-text retrieval
- normalizers.py: Clinical trial normalization
- types.py: Common types and constants
"""

# Main pipeline function - primary public interface
from .pipeline import enhanced_retrieval

# Individual components for advanced usage
from .query_optimizer import optimize_query
from .ranking import deduplicate_papers, rank_by_relevance
from .llm_filter import filter_by_llm_relevance_parallel
from .fulltext_enrichment import enrich_with_fulltext
from .normalizers import normalize_trial_to_paper

# Types for callers
from .types import ProgressCallback, _noop_callback

__all__ = [
    # Main pipeline
    "enhanced_retrieval",
    
    # Components
    "optimize_query",
    "deduplicate_papers",
    "rank_by_relevance",
    "filter_by_llm_relevance_parallel",
    "enrich_with_fulltext",
    "normalize_trial_to_paper",
    
    # Types
    "ProgressCallback",
]
