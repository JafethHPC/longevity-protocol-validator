from langchain_core.tools import tool
from typing import List
from app.ingestion import search_pubmed_ids, fetch_details_batch, ingest_paper_batch
from app.pdf_fetcher import get_pmc_id, download_pdf
from app.ingest_pdf import process_pdf
from pathlib import Path
import concurrent.futures
from app.text_processor import ingest_full_text

def process_single_paper(pmid: str, topic: str, save_dir: Path) -> str:
    """
    Independent worker function:
    1. Checks for OA PDF
    2. Downloads it
    3. Runs Vision Analysis
    Returns a success message or None
    """
    try:
        pmc_id = get_pmc_id(pmid)
        if not pmc_id:
            return None
        
        save_path = str(save_dir / f"{pmid}.pdf")

        if download_pdf(pmc_id, save_path):
            title = str(pmid)
            try:
                process_pdf(save_path, title)
            except Exception as e:
                print(f"Error processing {pmid}: {e}")
                return None
            try:
                ingest_full_text(save_path, pmid, title)
            except Exception as e:
                print(f"Error processing {pmid}: {e}")
                return None
            return f"Processed {topic} (ID: {pmid})"
        else:
            return None
    except Exception as e:
        print(f"Error processing {pmid}: {e}")
        return None

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
    
    base_path = Path(__file__).parent.parent
    save_dir = base_path / "static" / "figures"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    processed_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_pmid = {
            executor.submit(process_single_paper, pmid, topic, save_dir): pmid
            for pmid in ids[:10]
        }

        for future in concurrent.futures.as_completed(future_to_pmid):
            result = future.result()
            if result:
                processed_results.append(result)
                if len(processed_results) >= 10:    
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    if len(processed_results) == 0:
        return "I found relevant papers, but none were Open Access (Free PDF) so I could not extract images."

    return f"Success! I have processed {len(processed_results)} papers ({', '.join(processed_results)}), extracted figures, and analyzed them with AI vision."
    