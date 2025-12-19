"""
PubMed data source.

PubMed provides access to 36M+ biomedical literature citations.
- No API key required
- Uses Entrez/NCBI API
"""
from typing import List, Dict
from Bio import Entrez

# Set email for Entrez (required by NCBI)
Entrez.email = "researcher@example.com"


def search_pubmed(query: str, max_results: int = 50) -> List[Dict]:
    """Search PubMed and return papers with metadata."""
    print(f"---SEARCHING PUBMED: {query[:50]}...---")
    
    try:
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
                
                papers.append({
                    "title": str(article['ArticleTitle']),
                    "abstract": abstract,
                    "journal": str(article['Journal']['Title']),
                    "year": int(article['Journal']['JournalIssue']['PubDate'].get('Year', 0)),
                    "pmid": str(paper['MedlineCitation']['PMID']),
                    "source": "PubMed",
                    "is_review": is_review,
                    "citation_count": 0,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{paper['MedlineCitation']['PMID']}/"
                })
            except (KeyError, TypeError):
                continue
        
        print(f"  Returned {len(papers)} papers with abstracts")
        return papers
        
    except Exception as e:
        print(f"  PubMed error: {e}")
        return []
