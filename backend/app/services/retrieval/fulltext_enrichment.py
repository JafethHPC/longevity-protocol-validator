"""
Full-text enrichment for papers.

Retrieves full-text content from open access sources
for the most relevant papers.
"""
from typing import List, Dict

from app.core.logging import get_logger
from app.schemas.events import ProgressStep
from .types import ProgressCallback, _noop_callback

logger = get_logger(__name__)


def enrich_with_fulltext(
    papers: List[Dict], 
    max_papers_to_enrich: int = 10,
    on_progress: ProgressCallback = _noop_callback
) -> List[Dict]:
    """
    Enrich top papers with full text from open access sources.
    
    Only attempts full-text retrieval for the most relevant papers
    to balance quality improvement with API call limits.
    
    Args:
        papers: List of papers to potentially enrich
        max_papers_to_enrich: Maximum number of papers to attempt enrichment on
        on_progress: Progress callback
        
    Returns:
        Papers list with fulltext fields populated where available
    """
    from app.services.fulltext import fulltext_service
    
    logger.info("---ENRICHING WITH FULL TEXT---")
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
                logger.debug(f"✓ Full text for paper {i+1}: {result['word_count']} words from {result['source']}")
            else:
                paper['has_fulltext'] = False
        except Exception as e:
            logger.debug(f"✗ Failed to get full text for paper {i+1}: {e}")
            paper['has_fulltext'] = False
    
    for paper in papers[max_papers_to_enrich:]:
        paper['has_fulltext'] = False
    
    logger.info(f"FULL TEXT ENRICHMENT: {enriched_count}/{min(len(papers), max_papers_to_enrich)} papers ({total_fulltext_chars:,} chars)")
    on_progress(
        ProgressStep.FILTERING, 
        "Full-text retrieval complete", 
        f"{enriched_count} papers with full text"
    )
    
    return papers
