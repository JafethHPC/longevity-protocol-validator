"""
Main retrieval pipeline.

Orchestrates the full enhanced retrieval process:
1. Query optimization
2. Parallel source fetching
3. Deduplication
4. Semantic ranking
5. LLM-based filtering
6. Full-text enrichment
"""
import asyncio
import time
from typing import List, Dict, Optional

from app.core.logging import get_logger
from app.schemas.retrieval import ResearchConfig
from app.schemas.events import ProgressStep
from app.services.sources import (
    search_pubmed,
    search_openalex,
    search_europe_pmc,
    search_crossref,
    search_clinical_trials,
)

from .types import ProgressCallback, _noop_callback
from .normalizers import normalize_trial_to_paper
from .query_optimizer import optimize_query
from .ranking import deduplicate_papers, rank_by_relevance
from .llm_filter import filter_by_llm_relevance_parallel
from .fulltext_enrichment import enrich_with_fulltext

logger = get_logger(__name__)


async def _fetch_all_sources_async(
    pubmed_query: str,
    semantic_query: str,
    concept_query: str,
    config: ResearchConfig,
    on_progress: ProgressCallback
) -> List[Dict]:
    """
    Fetch papers from all sources in parallel using asyncio.
    
    Uses ResearchConfig to determine which sources to query and with what limits.
    
    Returns combined list of all papers from all sources.
    """
    tasks = []
    source_names = []
    
    # PubMed searches (main + concept query)
    if config.pubmed.enabled:
        tasks.append(search_pubmed(pubmed_query, max_results=config.pubmed.max_results))
        source_names.append("PubMed")
        tasks.append(search_pubmed(concept_query, max_results=config.pubmed.max_results))
        source_names.append("PubMed-Concepts")
    
    # OpenAlex searches (semantic + concept query)
    if config.openalex.enabled:
        tasks.append(search_openalex(semantic_query, max_results=config.openalex.max_results))
        source_names.append("OpenAlex")
        tasks.append(search_openalex(concept_query, max_results=config.openalex.max_results))
        source_names.append("OpenAlex-Concepts")
    
    # Europe PMC
    if config.europe_pmc.enabled:
        tasks.append(search_europe_pmc(semantic_query, max_results=config.europe_pmc.max_results))
        source_names.append("EuropePMC")
    
    # CrossRef
    if config.crossref.enabled:
        tasks.append(search_crossref(semantic_query, max_results=config.crossref.max_results))
        source_names.append("CrossRef")
    
    # Clinical Trials (uses concept_query - shorter for API compatibility)
    if config.clinical_trials.enabled:
        tasks.append(search_clinical_trials(concept_query, max_results=config.clinical_trials.max_results))
        source_names.append("ClinicalTrials.gov")
    
    if not tasks:
        logger.warning("No sources enabled in config!")
        return []
    
    # Run all searches in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results, handling any errors gracefully
    all_papers = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.debug(f"{source_names[i]} failed: {result}")
        else:
            # Normalize clinical trials to paper format
            if source_names[i] == "ClinicalTrials.gov":
                normalized = [normalize_trial_to_paper(t) for t in result]
                logger.debug(f"{source_names[i]}: {len(normalized)} clinical trials")
                all_papers.extend(normalized)
            else:
                logger.debug(f"{source_names[i]}: {len(result)} papers")
                all_papers.extend(result)
    
    on_progress(ProgressStep.SEARCHING_CROSSREF, "All sources searched", f"{len(all_papers)} total papers + trials")
    
    return all_papers


def _run_parallel_fetch(
    pubmed_query: str,
    semantic_query: str,
    concept_query: str,
    config: ResearchConfig,
    on_progress: ProgressCallback
) -> List[Dict]:
    """
    Sync wrapper to run the async parallel fetch.
    
    Uses asyncio.run() to execute the async function from sync context.
    This is safe because enhanced_retrieval is called from a thread
    (via FastAPI's background thread for sync endpoints).
    """
    return asyncio.run(_fetch_all_sources_async(
        pubmed_query,
        semantic_query,
        concept_query,
        config,
        on_progress
    ))


def enhanced_retrieval(
    user_query: str, 
    max_final_papers: int = 25,
    config: Optional[ResearchConfig] = None,
    on_progress: ProgressCallback = _noop_callback
) -> List[Dict]:
    """
    Full enhanced retrieval pipeline with parallel processing.
    
    Pipeline steps:
    1. Optimize query - Generate source-specific search queries
    2. Search multiple sources - Parallel async fetching
    3. Deduplicate - Remove duplicate papers
    4. Rank ALL papers by relevance - Semantic similarity + boosts
    5. LLM filter on top candidates - Batch parallel evaluation
    6. Enrich with full text (optional)
    
    Args:
        user_query: The research question from the user
        max_final_papers: Maximum number of papers to return (default 25, max 100)
            Note: This is overridden by config.max_final_sources if config is provided
        config: ResearchConfig controlling source limits and behavior
        on_progress: Callback function for progress updates
        
    Returns:
        List of highly relevant papers with metadata and optional full text
    """
    # Use provided config or create default
    if config is None:
        config = ResearchConfig.default()
    
    # Allow max_final_papers to override if explicitly different from default
    if max_final_papers != 25:
        max_sources = min(max_final_papers, 100)
    else:
        max_sources = config.max_final_sources
    
    logger.info(f"\n{'='*60}")
    logger.info(f"ENHANCED RETRIEVAL (PARALLEL): {user_query}")
    logger.info(f"Target sources: {max_sources} (min papers: {config.min_papers}, min trials: {config.min_clinical_trials})")
    logger.info(f"{'='*60}\n")
    
    optimized = optimize_query(user_query, on_progress)
    
    concept_query = " ".join(optimized.key_concepts[:3])
    
    # Log enabled sources
    enabled_sources = []
    if config.pubmed.enabled:
        enabled_sources.append(f"PubMed({config.pubmed.max_results})")
    if config.openalex.enabled:
        enabled_sources.append(f"OpenAlex({config.openalex.max_results})")
    if config.europe_pmc.enabled:
        enabled_sources.append(f"EuropePMC({config.europe_pmc.max_results})")
    if config.crossref.enabled:
        enabled_sources.append(f"CrossRef({config.crossref.max_results})")
    if config.clinical_trials.enabled:
        enabled_sources.append(f"ClinicalTrials({config.clinical_trials.max_results})")
    
    logger.info(f"SOURCES: {', '.join(enabled_sources)}")
    logger.info(f"CONCEPT SEARCH: {concept_query}")
    
    # Fetch all sources in parallel using asyncio
    on_progress(ProgressStep.SEARCHING_PUBMED, "Searching all sources in parallel...", None)
    
    start_time = time.time()
    
    all_papers = _run_parallel_fetch(
        optimized.pubmed_query,
        optimized.semantic_query, 
        concept_query,
        config,
        on_progress
    )
    
    elapsed = time.time() - start_time
    logger.info(f"\n---TOTAL CANDIDATES: {len(all_papers)} (fetched in {elapsed:.1f}s)---")
    
    if not all_papers:
        return []
    
    on_progress(ProgressStep.DEDUPLICATING, "Removing duplicate papers...", f"{len(all_papers)} total papers")
    unique_papers = deduplicate_papers(all_papers)
    logger.info(f"AFTER DEDUP: {len(unique_papers)}")
    on_progress(ProgressStep.DEDUPLICATING, "Removed duplicates", f"{len(unique_papers)} unique papers")
    
    papers_to_filter = max(max_sources * 3, 75)
    papers_to_filter = min(papers_to_filter, len(unique_papers))
    
    ranked_papers = rank_by_relevance(
        unique_papers, 
        user_query, 
        config=config,
        top_k=papers_to_filter,
        on_progress=on_progress
    )
    logger.info(f"SELECTED TOP {len(ranked_papers)} FOR LLM FILTERING")
    
    final_papers = filter_by_llm_relevance_parallel(
        ranked_papers, 
        user_query, 
        max_papers=max_sources, 
        on_progress=on_progress
    )
    
    # Enrich with full text if enabled
    if config.include_fulltext:
        final_papers = enrich_with_fulltext(final_papers, on_progress=on_progress)
    
    logger.info(f"\n---FINAL PAPERS: {len(final_papers)}---")
    for i, p in enumerate(final_papers, 1):
        has_ft = "✓" if p.get('has_fulltext') else "✗"
        logger.debug(f"{i}. [{p['year']}] {p['title'][:60]}... [FT:{has_ft}]")
        logger.debug(f"   Source: {p['source']}, Citations: {p['citation_count']}, PMID: {p.get('pmid', 'N/A')}")
    
    return final_papers
