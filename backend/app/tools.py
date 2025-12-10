from langchain_core.tools import tool
from typing import List
from app.ingestion import search_pubmed_ids, fetch_details_batch, ingest_paper_batch

@tool
def research_pubmed(topic: str) -> str:
    """
    Research a scientific topic on PubMed.
    1. Searches for the top 5 papers.
    2. Downloads the abstracts
    3. Ingests them into the Weaviate database.

    Use this tool when the user asks about a topic you don't have context for.
    """
    
    ids = search_pubmed_ids(topic, max_results=5)

    if not ids:
        return f"I searched PubMed for '{topic}' but found no papers."
    
    papers = fetch_details_batch(ids)

    if not papers:
        return "Found IDs but failed to download abstracts."
    
    ingest_paper_batch(papers)
    return f"Success! I have read and stored {len(papers)} papers about '{topic}'."