"""
Enhanced Multi-Source Retrieval System with Parallel Processing

Provides improved paper retrieval by:
1. Optimizing search queries for each source
2. Fetching from multiple sources (PubMed, OpenAlex, Europe PMC, CrossRef)
3. Ranking ALL papers by semantic similarity + citation count
4. Parallel batch LLM-based relevance filtering for speed
"""
import asyncio
from typing import List, Dict, Callable, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import numpy as np

from app.core.config import settings
from app.schemas.retrieval import OptimizedQueries, PaperRelevance, BatchPaperRelevance, ResearchConfig
from app.schemas.events import ProgressStep
from app.services.sources import (
    search_pubmed,
    search_openalex,
    search_europe_pmc,
    search_crossref,
    search_clinical_trials,
)

ProgressCallback = Callable[[ProgressStep, str, Optional[str]], None]

MAX_CONCURRENT_LLM_CALLS = 5
BATCH_SIZE = 8
# Note: per-source limits are now controlled by ResearchConfig


def _normalize_trial_to_paper(trial: Dict) -> Dict:
    """
    Convert a clinical trial record to the standard paper format.
    
    This allows clinical trials to be processed alongside research papers
    in the rest of the pipeline (ranking, filtering, display).
    """
    # Build a comprehensive abstract from trial data
    abstract_parts = []
    
    if trial.get('abstract'):
        abstract_parts.append(trial['abstract'])
    
    if trial.get('conditions'):
        abstract_parts.append(f"Conditions: {', '.join(trial['conditions'][:3])}")
    
    if trial.get('interventions'):
        abstract_parts.append(f"Interventions: {', '.join(trial['interventions'][:3])}")
    
    if trial.get('primary_outcomes'):
        abstract_parts.append(f"Primary outcomes: {', '.join(trial['primary_outcomes'][:2])}")
    
    if trial.get('enrollment'):
        abstract_parts.append(f"Enrollment: {trial['enrollment']} participants")
    
    if trial.get('phase') and trial['phase'] != 'N/A':
        abstract_parts.append(f"Phase: {trial['phase']}")
    
    abstract = " | ".join(abstract_parts) if abstract_parts else trial.get('title', '')
    
    return {
        'title': trial.get('title', ''),
        'abstract': abstract,
        'journal': 'ClinicalTrials.gov',
        'year': trial.get('year', 0) or 2024,
        'pmid': trial.get('nct_id', ''),  # Use NCT ID as identifier
        'doi': '',
        'source': 'ClinicalTrials.gov',
        'is_review': False,
        'citation_count': 0,  # Trials don't have citations
        'url': trial.get('url', ''),
        'type': 'clinical_trial',
        'status': trial.get('status', ''),
        'phase': trial.get('phase', ''),
        'has_results': trial.get('has_results', False),
        'conditions': trial.get('conditions', []),
        'interventions': trial.get('interventions', []),
    }



async def _fetch_all_sources_async(
    pubmed_query: str,
    semantic_query: str,
    concept_query: str,
    config: ResearchConfig,
    on_progress: 'ProgressCallback'
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
        print("  WARNING: No sources enabled in config!")
        return []
    
    # Run all searches in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results, handling any errors gracefully
    all_papers = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"  {source_names[i]} failed: {result}")
        else:
            # Normalize clinical trials to paper format
            if source_names[i] == "ClinicalTrials.gov":
                normalized = [_normalize_trial_to_paper(t) for t in result]
                print(f"  {source_names[i]}: {len(normalized)} clinical trials")
                all_papers.extend(normalized)
            else:
                print(f"  {source_names[i]}: {len(result)} papers")
                all_papers.extend(result)
    
    on_progress(ProgressStep.SEARCHING_CROSSREF, "All sources searched", f"{len(all_papers)} total papers + trials")
    
    return all_papers


def _run_parallel_fetch(
    pubmed_query: str,
    semantic_query: str,
    concept_query: str,
    config: ResearchConfig,
    on_progress: 'ProgressCallback'
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


def _noop_callback(step: ProgressStep, message: str, detail: Optional[str] = None):
    """Default no-op callback when none provided."""
    pass


def optimize_query(user_query: str, on_progress: ProgressCallback = _noop_callback) -> OptimizedQueries:
    """Convert user question into optimized search queries for PubMed and Semantic Scholar."""
    on_progress(ProgressStep.OPTIMIZING, "Optimizing search queries...", None)
    
    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0, 
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(OptimizedQueries)
    
    prompt = f"""Convert this research question into comprehensive, optimized search queries.

User question: {user_query}

CRITICAL REQUIREMENTS:
1. If the question contains specific numbers, dosages, or time durations (like "7-8 hours", "500mg", "3 times per week"), YOU MUST include these in BOTH queries.
2. Include SYNONYMS and RELATED TERMS for the main concepts.
3. Think about the UNDERLYING MECHANISMS and include those terms too.

For PubMed query:
- Use MeSH terms where appropriate (e.g., "fasting"[MeSH], "insulin resistance"[MeSH])
- Use AND/OR boolean operators to combine concepts
- Include ALL relevant synonyms (e.g., for "intermittent fasting" also include "time-restricted eating", "alternate day fasting")
- Add mechanism-related terms (e.g., for fasting: "autophagy", "insulin sensitivity", "ketosis", "metabolic switch")

For Semantic Search query:
- Use natural scientific language with comprehensive terminology
- Include mechanism-related terms and biological pathways
- Add related outcome measures and biomarkers

For Key Concepts (extract 5-8 terms):
- Include the main topic
- Include specific mechanisms (e.g., "autophagy", "mTOR", "AMPK")
- Include relevant biomarkers (e.g., "cortisol", "insulin", "glucose")
- Include related interventions or treatments
- Include outcome measures

EXAMPLE for "intermittent fasting metabolic health":
- PubMed: (intermittent fasting[MeSH] OR time-restricted feeding OR alternate day fasting) AND (metabolic health[MeSH] OR insulin sensitivity OR glucose metabolism OR autophagy)
- Semantic: intermittent fasting metabolic effects insulin sensitivity glucose regulation autophagy ketosis circadian rhythm
- Concepts: ["intermittent fasting", "insulin sensitivity", "autophagy", "glucose metabolism", "ketosis", "circadian rhythm", "metabolic syndrome"]"""

    result = llm.invoke(prompt)
    print(f"---QUERY OPTIMIZATION---")
    print(f"  PubMed: {result.pubmed_query}")
    print(f"  Semantic: {result.semantic_query}")
    print(f"  Concepts: {result.key_concepts}")
    return result


def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """Remove duplicate papers based on title similarity and PMID."""
    seen_titles = set()
    seen_pmids = set()
    unique_papers = []
    
    for paper in papers:
        pmid = paper.get('pmid', '')
        if pmid and pmid in seen_pmids:
            continue
        
        title_key = paper['title'].lower().strip()[:60]
        if title_key in seen_titles:
            continue
        
        if pmid:
            seen_pmids.add(pmid)
        seen_titles.add(title_key)
        unique_papers.append(paper)
    
    return unique_papers


def rank_by_relevance(
    papers: List[Dict], 
    query: str, 
    config: ResearchConfig,
    top_k: Optional[int] = None,
    on_progress: ProgressCallback = _noop_callback
) -> List[Dict]:
    """
    Rank ALL papers by semantic similarity to the query + citation count.
    
    Args:
        papers: List of papers to rank
        query: User's research question
        config: Research configuration with boost settings and minimum counts
        top_k: If provided, return only top k papers. If None, return ALL ranked papers.
        on_progress: Progress callback
    """
    if not papers:
        return []
    
    on_progress(ProgressStep.RANKING, "Ranking papers by relevance...", f"{len(papers)} papers to analyze")
    print(f"---RANKING ALL {len(papers)} PAPERS BY RELEVANCE---")
    
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
    
    query_embedding = embeddings.embed_query(query)
    paper_texts = [f"{p['title']}. {p['abstract'][:500]}" for p in papers]
    paper_embeddings = embeddings.embed_documents(paper_texts)
    
    query_vec = np.array(query_embedding)
    
    for i, paper in enumerate(papers):
        paper_vec = np.array(paper_embeddings[i])
        similarity = np.dot(query_vec, paper_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(paper_vec)
        )
        
        citation_boost = min(paper['citation_count'] / 1000, 0.2)
        review_boost = 0.1 if paper['is_review'] else 0
        
        # Clinical trials get a configurable boost to compete with highly-cited papers
        # They're valuable for dosing/protocol info even without citations
        is_clinical_trial = paper.get('type') == 'clinical_trial' or paper.get('pmid', '').startswith('NCT')
        trial_boost = config.clinical_trial_boost if is_clinical_trial else 0
        
        paper['relevance_score'] = similarity + citation_boost + review_boost + trial_boost
    
    ranked = sorted(papers, key=lambda x: x['relevance_score'], reverse=True)
    
    # Ensure diversity: include minimum clinical trials even if they rank lower
    min_trials = config.min_clinical_trials
    trials_in_top = [p for p in ranked[:top_k] if p.get('type') == 'clinical_trial' or p.get('pmid', '').startswith('NCT')]
    
    if len(trials_in_top) < min_trials:
        # Find more clinical trials from the rest of the ranked list
        remaining_trials = [p for p in ranked[top_k:] if p.get('type') == 'clinical_trial' or p.get('pmid', '').startswith('NCT')]
        trials_to_add = remaining_trials[:min_trials - len(trials_in_top)]
        
        if trials_to_add:
            # Replace lowest-ranked papers with clinical trials
            ranked = ranked[:top_k - len(trials_to_add)] + trials_to_add if top_k else ranked
            print(f"  Added {len(trials_to_add)} clinical trials to ensure diversity")
    
    print(f"  Top 10 after ranking:")
    for p in ranked[:10]:
        trial_marker = "[TRIAL]" if p.get('type') == 'clinical_trial' or p.get('pmid', '').startswith('NCT') else ""
        print(f"    [{p['relevance_score']:.3f}] {trial_marker} {p['title'][:55]}...")
    
    if top_k is not None:
        return ranked[:top_k]
    return ranked


def _evaluate_paper_batch(
    papers: List[Dict], 
    user_query: str, 
    llm: ChatOpenAI
) -> List[Tuple[Dict, bool, str]]:
    """
    Evaluate a batch of papers in a single LLM call.
    Returns list of (paper, is_relevant, reason) tuples.
    """
    if not papers:
        return []
    
    papers_text = ""
    for i, paper in enumerate(papers):
        papers_text += f"""
PAPER {i+1}:
Title: {paper['title']}
Abstract: {paper['abstract'][:600]}
Year: {paper['year']} | Citations: {paper['citation_count']}
---
"""
    
    prompt = f"""Evaluate each paper's relevance to the research question.

QUESTION: {user_query}

{papers_text}

For EACH paper, determine if it contains useful information to answer the question.
Be inclusive - if there's related information, mark as relevant.
Respond with the paper number, relevance (true/false), and a brief reason for EACH paper."""

    try:
        result = llm.invoke(prompt)
        return _parse_batch_response(papers, result)
    except Exception as e:
        print(f"  Batch evaluation error: {e}")
        return [(p, True, "Error during evaluation - included by default") for p in papers]


def _parse_batch_response(papers: List[Dict], result: BatchPaperRelevance) -> List[Tuple[Dict, bool, str]]:
    """Parse the structured batch response."""
    parsed = []
    
    for i, paper in enumerate(papers):
        if i < len(result.evaluations):
            eval_result = result.evaluations[i]
            parsed.append((paper, eval_result.is_relevant, eval_result.reason))
        else:
            parsed.append((paper, True, "Not evaluated - included by default"))
    
    return parsed


def filter_by_llm_relevance_parallel(
    papers: List[Dict], 
    user_query: str, 
    max_papers: int = 25,
    on_progress: ProgressCallback = _noop_callback
) -> List[Dict]:
    """
    Use parallel batch LLM calls to filter papers based on relevance.
    
    This processes papers in batches of BATCH_SIZE, with MAX_CONCURRENT_LLM_CALLS
    running in parallel for significant speed improvements.
    """
    if len(papers) <= max_papers:
        for paper in papers:
            if 'relevance_reason' not in paper:
                paper['relevance_reason'] = "High relevance score"
        return papers
    
    on_progress(ProgressStep.FILTERING, "Filtering papers with AI...", f"Analyzing {len(papers)} papers in parallel")
    print(f"---PARALLEL LLM FILTERING {len(papers)} PAPERS (batch_size={BATCH_SIZE}, concurrency={MAX_CONCURRENT_LLM_CALLS})---")
    
    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0, 
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(BatchPaperRelevance)
    
    batches = [papers[i:i+BATCH_SIZE] for i in range(0, len(papers), BATCH_SIZE)]
    print(f"  Created {len(batches)} batches of up to {BATCH_SIZE} papers each")
    
    all_results = []
    
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_LLM_CALLS) as executor:
        futures = [
            executor.submit(_evaluate_paper_batch, batch, user_query, llm)
            for batch in batches
        ]
        
        for i, future in enumerate(futures):
            try:
                batch_results = future.result(timeout=60)
                all_results.extend(batch_results)
                print(f"  Batch {i+1}/{len(batches)} complete: {sum(1 for _, rel, _ in batch_results if rel)} relevant")
            except Exception as e:
                print(f"  Batch {i+1} failed: {e}")
                all_results.extend([(p, True, "Batch failed - included") for p in batches[i]])
    
    relevant_papers = []
    for paper, is_relevant, reason in all_results:
        if is_relevant:
            paper['relevance_reason'] = reason
            relevant_papers.append(paper)
    
    relevant_papers.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    final_papers = relevant_papers[:max_papers]
    
    print(f"  {len(relevant_papers)} papers marked relevant, returning top {len(final_papers)}")
    return final_papers


def filter_by_llm_relevance(
    papers: List[Dict], 
    user_query: str, 
    max_papers: int = 10,
    on_progress: ProgressCallback = _noop_callback
) -> List[Dict]:
    """
    Legacy sequential filter - kept for backwards compatibility.
    Use filter_by_llm_relevance_parallel for better performance.
    """
    return filter_by_llm_relevance_parallel(papers, user_query, max_papers, on_progress)


def enhanced_retrieval(
    user_query: str, 
    max_final_papers: int = 25,
    config: Optional[ResearchConfig] = None,
    on_progress: ProgressCallback = _noop_callback
) -> List[Dict]:
    """
    Full enhanced retrieval pipeline with parallel processing:
    1. Optimize query
    2. Search multiple sources (more papers per source)
    3. Deduplicate
    4. Rank ALL papers by relevance
    5. Parallel batch LLM filter on top candidates
    
    Args:
        user_query: The research question from the user
        max_final_papers: Maximum number of papers to return (default 25, max 100)
            Note: This is overridden by config.max_final_sources if config is provided
        config: ResearchConfig controlling source limits and behavior
        on_progress: Callback function for progress updates
    """
    # Use provided config or create default
    if config is None:
        config = ResearchConfig.default()
    
    # Allow max_final_papers to override if explicitly different from default
    if max_final_papers != 25:
        max_sources = min(max_final_papers, 100)
    else:
        max_sources = config.max_final_sources
    
    print(f"\n{'='*60}")
    print(f"ENHANCED RETRIEVAL (PARALLEL): {user_query}")
    print(f"Target sources: {max_sources} (min papers: {config.min_papers}, min trials: {config.min_clinical_trials})")
    print(f"{'='*60}\n")
    
    optimized = optimize_query(user_query, on_progress)
    
    concept_query = " ".join(optimized.key_concepts[:3])
    
    # Print enabled sources
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
    
    print(f"---SOURCES: {', '.join(enabled_sources)}---")
    print(f"---CONCEPT SEARCH: {concept_query}---")
    
    # Fetch all sources in parallel using asyncio
    on_progress(ProgressStep.SEARCHING_PUBMED, "Searching all sources in parallel...", None)
    
    import time
    start_time = time.time()
    
    all_papers = _run_parallel_fetch(
        optimized.pubmed_query,
        optimized.semantic_query, 
        concept_query,
        config,
        on_progress
    )
    
    elapsed = time.time() - start_time
    print(f"\n---TOTAL CANDIDATES: {len(all_papers)} (fetched in {elapsed:.1f}s)---")
    
    if not all_papers:
        return []
    
    on_progress(ProgressStep.DEDUPLICATING, "Removing duplicate papers...", f"{len(all_papers)} total papers")
    unique_papers = deduplicate_papers(all_papers)
    print(f"---AFTER DEDUP: {len(unique_papers)}---")
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
    print(f"---SELECTED TOP {len(ranked_papers)} FOR LLM FILTERING---")
    
    final_papers = filter_by_llm_relevance_parallel(
        ranked_papers, 
        user_query, 
        max_papers=max_sources, 
        on_progress=on_progress
    )
    
    # Enrich with full text if enabled
    if config.include_fulltext:
        final_papers = enrich_with_fulltext(final_papers, on_progress=on_progress)
    
    print(f"\n---FINAL PAPERS: {len(final_papers)}---")
    for i, p in enumerate(final_papers, 1):
        has_ft = "✓" if p.get('has_fulltext') else "✗"
        print(f"  {i}. [{p['year']}] {p['title'][:60]}... [FT:{has_ft}]")
        print(f"     Source: {p['source']}, Citations: {p['citation_count']}, PMID: {p.get('pmid', 'N/A')}")
    
    return final_papers


def enrich_with_fulltext(
    papers: List[Dict], 
    max_papers_to_enrich: int = 10,
    on_progress: ProgressCallback = _noop_callback
) -> List[Dict]:
    """
    Enrich top papers with full text from open access sources.
    
    Only attempts full-text retrieval for the most relevant papers
    to balance quality improvement with API call limits.
    """
    from app.services.fulltext import fulltext_service
    
    print(f"\n---ENRICHING WITH FULL TEXT---")
    on_progress(ProgressStep.FILTERING, "Retrieving full-text for top papers...", None)
    
    enriched_count = 0
    total_fulltext_chars = 0
    
    for i, paper in enumerate(papers[:max_papers_to_enrich]):
        pmid = paper.get('pmid', '')
        doi = paper.get('doi', '')
        
        if not pmid and not doi:
            paper['has_fulltext'] = False
            continue
        
        try:
            result = fulltext_service.get_full_text(pmid=pmid, doi=doi)
            
            if result and result['char_count'] > len(paper.get('abstract', '')):
                paper['fulltext'] = result['text']
                paper['fulltext_source'] = result['source']
                paper['has_fulltext'] = True
                enriched_count += 1
                total_fulltext_chars += result['char_count']
                print(f"  ✓ Full text for paper {i+1}: {result['word_count']} words from {result['source']}")
            else:
                paper['has_fulltext'] = False
        except Exception as e:
            print(f"  ✗ Failed to get full text for paper {i+1}: {e}")
            paper['has_fulltext'] = False
    
    for paper in papers[max_papers_to_enrich:]:
        paper['has_fulltext'] = False
    
    print(f"---FULL TEXT ENRICHMENT: {enriched_count}/{min(len(papers), max_papers_to_enrich)} papers ({total_fulltext_chars:,} chars)---")
    on_progress(
        ProgressStep.FILTERING, 
        "Full-text retrieval complete", 
        f"{enriched_count} papers with full text"
    )
    
    return papers
