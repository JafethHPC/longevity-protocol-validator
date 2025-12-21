"""
PubMed data source.

PubMed provides access to 36M+ biomedical literature citations.
- No API key required
- Uses Entrez/NCBI API via Biopython

Note: Biopython's Entrez library is synchronous. We wrap it in an
async function that runs in a ThreadPoolExecutor to avoid blocking
the event loop while still enabling parallel fetching with other sources.
"""
from typing import List, Dict
from Bio import Entrez
import asyncio
from concurrent.futures import ThreadPoolExecutor

Entrez.email = "researcher@example.com"

# Shared executor for running sync Entrez calls
_executor = ThreadPoolExecutor(max_workers=2)


def _search_pubmed_sync(query: str, max_results: int = 50) -> List[Dict]:
    """
    Synchronous PubMed search implementation.
    
    This is the actual search logic using Biopython's Entrez.
    It's wrapped by the async search_pubmed function.
    """
    print(f"---SEARCHING PUBMED: {query[:50]}...---")
    
    try:
        # Search for paper IDs
        handle = Entrez.esearch(
            db="pubmed", 
            term=query, 
            retmax=max_results,
            sort="relevance"
        )
        record = Entrez.read(handle)
        handle.close()
        
        ids = record.get("IdList", [])
        if not ids:
            print(f"  No results found")
            return []
        
        print(f"  Found {len(ids)} papers")
        
        # Fetch full records
        handle = Entrez.efetch(db="pubmed", id=",".join(ids), retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        
        papers = []
        for paper in records.get('PubmedArticle', []):
            try:
                article = paper['MedlineCitation']['Article']
                abstract_list = article.get('Abstract', {}).get('AbstractText', [])
                abstract = " ".join(str(a) for a in abstract_list)
                
                if not abstract or len(abstract) < 100:
                    continue
                
                pub_types = article.get('PublicationTypeList', [])
                pub_type_names = [str(pt) for pt in pub_types]
                is_review = any('review' in pt.lower() for pt in pub_type_names)
                
                # Extract DOI if available
                article_ids = paper['MedlineCitation'].get('Article', {}).get('ELocationID', [])
                doi = ""
                for eid in article_ids:
                    if eid.attributes.get('EIdType') == 'doi':
                        doi = str(eid)
                        break
                
                pmid = str(paper['MedlineCitation']['PMID'])
                
                papers.append({
                    "title": str(article['ArticleTitle']),
                    "abstract": abstract,
                    "journal": str(article['Journal']['Title']),
                    "year": int(article['Journal']['JournalIssue']['PubDate'].get('Year', 0)),
                    "pmid": pmid,
                    "doi": doi,
                    "source": "PubMed",
                    "is_review": is_review,
                    "citation_count": 0,  # PubMed doesn't provide citation counts
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                })
            except (KeyError, TypeError):
                continue
        
        print(f"  Returned {len(papers)} papers with abstracts")
        return papers
        
    except Exception as e:
        print(f"  PubMed error: {e}")
        return []


async def search_pubmed(query: str, max_results: int = 50) -> List[Dict]:
    """
    Search PubMed and return papers with metadata.
    
    This is an async wrapper around the synchronous Entrez library.
    Uses a ThreadPoolExecutor to run the blocking I/O without
    blocking the asyncio event loop.
    
    Can be used with asyncio.gather() for parallel fetching.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, 
        _search_pubmed_sync, 
        query, 
        max_results
    )
