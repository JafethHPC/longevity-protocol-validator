"""
Paper ranking and deduplication.

Handles semantic similarity ranking and duplicate removal
for the retrieval pipeline.
"""
from typing import List, Dict, Optional
import numpy as np
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.retrieval import ResearchConfig
from app.schemas.events import ProgressStep
from .types import ProgressCallback, _noop_callback

logger = get_logger(__name__)


def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """
    Remove duplicate papers based on title similarity and PMID.
    
    Deduplication is essential because we fetch from multiple sources
    and the same paper may appear in PubMed, OpenAlex, and CrossRef.
    
    Args:
        papers: List of papers to deduplicate
        
    Returns:
        List of unique papers
    """
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
    
    Uses embeddings to compute semantic similarity between the query
    and each paper's title + abstract. Also factors in:
    - Citation count (highly cited papers get a boost)
    - Review status (reviews get a small boost)
    - Clinical trial status (configurable boost for diversity)
    
    Args:
        papers: List of papers to rank
        query: User's research question
        config: Research configuration with boost settings and minimum counts
        top_k: If provided, return only top k papers. If None, return ALL ranked papers.
        on_progress: Progress callback
        
    Returns:
        Sorted list of papers with relevance_score field populated
    """
    if not papers:
        return []
    
    on_progress(ProgressStep.RANKING, "Ranking papers by relevance...", f"{len(papers)} papers to analyze")
    logger.info(f"RANKING ALL {len(papers)} PAPERS BY RELEVANCE")
    
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
            logger.debug(f"Added {len(trials_to_add)} clinical trials to ensure diversity")
    
    logger.debug("Top 10 after ranking:")
    for p in ranked[:10]:
        trial_marker = "[TRIAL]" if p.get('type') == 'clinical_trial' or p.get('pmid', '').startswith('NCT') else ""
        logger.debug(f"  [{p['relevance_score']:.3f}] {trial_marker} {p['title'][:55]}...")
    
    if top_k is not None:
        return ranked[:top_k]
    return ranked
