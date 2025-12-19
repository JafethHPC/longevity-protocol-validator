"""
OpenAlex data source.

OpenAlex provides access to 250M+ scholarly works.
- 100,000 calls per day
- 10 requests per second
- No API key required
"""
from typing import List, Dict
import requests
import time


def search_openalex(query: str, max_results: int = 50) -> List[Dict]:
    """
    Search OpenAlex API for papers.
    
    OpenAlex is free with generous rate limits:
    - 100,000 calls per day
    - 10 requests per second
    - No API key required
    """
    print(f"---SEARCHING OPENALEX: {query[:50]}...---")
    
    headers = {
        "User-Agent": "ResearchReportGenerator/1.0 (mailto:researcher@example.com)"
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
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 429:
            print("  Rate limited, waiting 1 second...")
            time.sleep(1)
            response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"  Error: {response.status_code}")
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
            
            ids = work.get("ids") or {}
            pmid = ids.get("pmid", "").replace("https://pubmed.ncbi.nlm.nih.gov/", "").strip("/")
            
            papers.append({
                "title": work.get("title", "") or work.get("display_name", ""),
                "abstract": abstract,
                "journal": journal,
                "year": work.get("publication_year", 0) or 0,
                "pmid": pmid,
                "source": "OpenAlex",
                "is_review": False,
                "citation_count": work.get("cited_by_count", 0) or 0,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else work.get("id", "")
            })
        
        print(f"  Returned {len(papers)} papers with abstracts")
        return papers
        
    except Exception as e:
        print(f"  OpenAlex error: {e}")
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
