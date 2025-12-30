"""
OpenAlex data source.

OpenAlex provides access to 250M+ scholarly works.
- 100,000 calls per day
- 10 requests per second
- No API key required

Uses httpx.AsyncClient for non-blocking HTTP requests,
enabling parallel fetching with other data sources.
"""
from typing import List, Dict
import httpx
import asyncio

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


async def search_openalex(query: str, max_results: int = 50) -> List[Dict]:
    """
    Search OpenAlex API for papers.
    
    OpenAlex is free with generous rate limits:
    - 100,000 calls per day
    - 10 requests per second
    - No API key required
    
    This is an async function that should be awaited.
    Use asyncio.gather() to run in parallel with other sources.
    """
    logger.info(f"Searching OpenAlex: {query[:50]}...")
    
    headers = {
        "User-Agent": f"ResearchReportGenerator/1.0 (mailto:{settings.API_CONTACT_EMAIL})"
    }
    
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per_page": min(max_results, 100),
        "filter": "has_abstract:true,type:article",
        "sort": "cited_by_count:desc",
        "select": "id,title,abstract_inverted_index,publication_year,cited_by_count,primary_location,authorships,ids"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)
            
            # Handle rate limiting with retry
            if response.status_code == 429:
                logger.warning("OpenAlex rate limited, waiting 1 second...")
                await asyncio.sleep(1)
                response = await client.get(url, params=params, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"OpenAlex error: HTTP {response.status_code}")
                return []
            
            data = response.json()
            papers = []
            
            for work in data.get("results", []):
                abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
                if not abstract or len(abstract) < 100:
                    continue
                
                primary_location = work.get("primary_location") or {}
                source = primary_location.get("source") or {}
                journal = source.get("display_name", "")
                
                # Extract identifiers
                ids = work.get("ids") or {}
                pmid = ids.get("pmid", "").replace("https://pubmed.ncbi.nlm.nih.gov/", "").strip("/")
                doi = ids.get("doi", "").replace("https://doi.org/", "")
                
                papers.append({
                    "title": work.get("title", "") or work.get("display_name", ""),
                    "abstract": abstract,
                    "journal": journal,
                    "year": work.get("publication_year", 0) or 0,
                    "pmid": pmid,
                    "doi": doi,
                    "source": "OpenAlex",
                    "is_review": False,
                    "citation_count": work.get("cited_by_count", 0) or 0,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else work.get("id", "")
                })
            
            logger.info(f"OpenAlex: Returned {len(papers)} papers with abstracts")
            return papers
        
    except httpx.TimeoutException:
        logger.error("OpenAlex timeout")
        return []
    except Exception as e:
        logger.error(f"OpenAlex error: {e}")
        return []


def _reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract text from OpenAlex inverted index format."""
    if not inverted_index:
        return ""
    
    try:
        words_with_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                words_with_positions.append((pos, word))
        
        words_with_positions.sort(key=lambda x: x[0])
        return " ".join(word for _, word in words_with_positions)
    except Exception:
        return ""
