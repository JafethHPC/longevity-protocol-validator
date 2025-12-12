from langchain_core.tools import tool
from typing import List
from app.ingestion import search_pubmed_ids, fetch_details_batch, ingest_paper_batch
from app.pdf_fetcher import get_pmc_id, download_pdf
from app.ingest_pdf import process_pdf
from pathlib import Path

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

@tool
def research_visuals(topic: str) -> str:
    """
    Finds scientific papers about a topic, downloads PDFs (if Open Access), 
    extracts charts/figures, and analyzes them with AI vision.
    Use this when the user asks for "Charts", "Figures", or "Visuals".
    """
    ids = search_pubmed_ids(topic, max_results=20)
    if not ids:
        return "No papers found."
    
    processed_count = 0
    max_papers = 3
    results_summary = []
    
    for pmid in ids:
        if processed_count >= max_papers:
            break

        pmc_id = get_pmc_id(pmid)

        if pmc_id:
            base_path = Path(__file__).parent.parent
            save_dir = base_path / "static" / "figures"
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = str(save_dir / f"{pmid}.pdf")

            if download_pdf(pmc_id, save_path):
                title =str(pmid)
                try:
                    process_pdf(save_path, title)
                    processed_count += 1
                    results_summary.append(f"processed {topic} (ID: {pmid})")
                except Exception as e:
                    print(f"Error processing {pmid}: {e}")
    
    if processed_count == 0:
        return "I found relevant papers, but none were Open Access (Free PDF) so I could not extract images."

    return f"Success! I have processed {processed_count} papers ({', '.join(results_summary)}), extracted figures, and analyzed them with AI vision."
    