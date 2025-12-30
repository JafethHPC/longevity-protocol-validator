"""
LLM-based relevance filtering.

Uses parallel batch LLM calls to filter papers based on
their relevance to the research question.
"""
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor

from app.core.logging import get_logger
from app.schemas.retrieval import BatchPaperRelevance
from app.schemas.events import ProgressStep
from app.services.llm import get_llm
from .types import ProgressCallback, _noop_callback, MAX_CONCURRENT_LLM_CALLS, BATCH_SIZE

logger = get_logger(__name__)


def _evaluate_paper_batch(
    papers: List[Dict], 
    user_query: str, 
    llm
) -> List[Tuple[Dict, bool, str]]:
    """
    Evaluate a batch of papers in a single LLM call.
    
    Args:
        papers: Batch of papers to evaluate
        user_query: The research question
        llm: Configured LLM client
        
    Returns:
        List of (paper, is_relevant, reason) tuples.
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
        logger.debug(f"Batch evaluation error: {e}")
        return [(p, True, "Error during evaluation - included by default") for p in papers]


def _parse_batch_response(
    papers: List[Dict], 
    result: BatchPaperRelevance
) -> List[Tuple[Dict, bool, str]]:
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
    
    Args:
        papers: Pre-ranked papers to filter
        user_query: The research question
        max_papers: Maximum number of papers to return
        on_progress: Progress callback
        
    Returns:
        Filtered list of relevant papers, up to max_papers
    """
    if len(papers) <= max_papers:
        for paper in papers:
            if 'relevance_reason' not in paper:
                paper['relevance_reason'] = "High relevance score"
        return papers
    
    on_progress(ProgressStep.FILTERING, "Filtering papers with AI...", f"Analyzing {len(papers)} papers in parallel")
    logger.info(f"PARALLEL LLM FILTERING {len(papers)} PAPERS (batch_size={BATCH_SIZE}, concurrency={MAX_CONCURRENT_LLM_CALLS})")
    
    llm = get_llm().with_structured_output(BatchPaperRelevance)
    
    batches = [papers[i:i+BATCH_SIZE] for i in range(0, len(papers), BATCH_SIZE)]
    logger.debug(f"Created {len(batches)} batches of up to {BATCH_SIZE} papers each")
    
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
                logger.debug(f"Batch {i+1}/{len(batches)} complete: {sum(1 for _, rel, _ in batch_results if rel)} relevant")
            except Exception as e:
                logger.debug(f"Batch {i+1} failed: {e}")
                all_results.extend([(p, True, "Batch failed - included") for p in batches[i]])
    
    relevant_papers = []
    for paper, is_relevant, reason in all_results:
        if is_relevant:
            paper['relevance_reason'] = reason
            relevant_papers.append(paper)
    
    relevant_papers.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    final_papers = relevant_papers[:max_papers]
    
    logger.debug(f"{len(relevant_papers)} papers marked relevant, returning top {len(final_papers)}")
    return final_papers
