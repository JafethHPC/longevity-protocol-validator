"""
Europe PMC data source.

Europe PMC provides access to 43M+ life science articles.
- No API key required
- Includes preprints from bioRxiv/medRxiv
- Focus on biomedical and health research
"""
from typing import List, Dict
import requests


def search_europe_pmc(query: str, max_results: int = 50) -> List[Dict]:
    """
    Search Europe PMC for life science papers.
    
    Europe PMC provides access to 43M+ life science articles.
    - No API key required
    - Includes preprints from bioRxiv/medRxiv
    - Focus on biomedical and health research
    """
    print(f"---SEARCHING EUROPE PMC: {query[:50]}...---")
    
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": query,
        "format": "json",
        "pageSize": min(max_results, 100),
        "resultType": "core",
        "sort": "CITED desc"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"  Error: {response.status_code}")
            return []
        
        data = response.json()
        papers = []
        
        for result in data.get("resultList", {}).get("result", []):
            abstract = result.get("abstractText", "")
            if not abstract or len(abstract) < 100:
                continue
            
            pmid = result.get("pmid", "")
            
            papers.append({
                "title": result.get("title", ""),
                "abstract": abstract,
                "journal": result.get("journalTitle", ""),
                "year": int(result.get("pubYear", 0) or 0),
                "pmid": pmid,
                "source": "EuropePMC",
                "is_review": result.get("pubType", "") == "review",
                "citation_count": int(result.get("citedByCount", 0) or 0),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else result.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url", "")
            })
        
        print(f"  Returned {len(papers)} papers with abstracts")
        return papers
        
    except Exception as e:
        print(f"  Europe PMC error: {e}")
        return []
