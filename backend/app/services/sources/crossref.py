"""
CrossRef data source.

CrossRef provides DOI metadata for 140M+ works.
- No API key required (use polite pool with email)
- Great for citation data

Uses httpx.AsyncClient for non-blocking HTTP requests.
"""
from typing import List, Dict
import httpx
import re


async def search_crossref(query: str, max_results: int = 50) -> List[Dict]:
    """
    Search CrossRef for scholarly works metadata.
    
    CrossRef provides DOI metadata for 140M+ works.
    - No API key required (use polite pool with email)
    - Great for citation data
    
    This is an async function - use asyncio.gather() to run in parallel.
    """
    print(f"---SEARCHING CROSSREF: {query[:50]}...---")
    
    headers = {
        "User-Agent": "ResearchReportGenerator/1.0 (mailto:researcher@example.com)"
    }
    
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "rows": min(max_results, 100),
        "filter": "has-abstract:true,type:journal-article",
        "sort": "is-referenced-by-count",
        "order": "desc"
    }
    
    try:
        # CrossRef can be slow, use longer timeout
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code != 200:
                print(f"  Error: {response.status_code}")
                return []
            
            data = response.json()
            papers = []
            
            for item in data.get("message", {}).get("items", []):
                abstract = item.get("abstract", "")
                # CrossRef abstracts may contain HTML tags
                if abstract:
                    abstract = re.sub(r'<[^>]+>', '', abstract).strip()
                
                if not abstract or len(abstract) < 100:
                    continue
                
                title = item.get("title", [""])[0] if item.get("title") else ""
                
                container = item.get("container-title", [""])
                journal = container[0] if container else ""
                
                published = item.get("published", {}).get("date-parts", [[0]])
                year = published[0][0] if published and published[0] else 0
                
                doi = item.get("DOI", "")
                
                papers.append({
                    "title": title,
                    "abstract": abstract,
                    "journal": journal,
                    "year": year,
                    "pmid": "",  # CrossRef doesn't have PMIDs
                    "doi": doi,
                    "source": "CrossRef",
                    "is_review": False,
                    "citation_count": item.get("is-referenced-by-count", 0) or 0,
                    "url": item.get("URL", "") or f"https://doi.org/{doi}" if doi else ""
                })
            
            print(f"  Returned {len(papers)} papers with abstracts")
            return papers
        
    except httpx.TimeoutException:
        print("  CrossRef timeout")
        return []
    except Exception as e:
        print(f"  CrossRef error: {e}")
        return []
