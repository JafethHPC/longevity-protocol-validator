from langchain_core.tools import tool
from typing import List
from app.ingestion import search_pubmed_ids, fetch_details_batch, ingest_paper_batch
from app.pdf_fetcher import get_pmc_id, download_pdf
from app.ingest_pdf import process_pdf
from pathlib import Path
import concurrent.futures
from app.text_processor import ingest_full_text

def process_single_paper(pmid: str, topic: str, save_dir: Path) -> dict:
    """
    Independent worker function:
    1. Checks for OA PDF
    2. Downloads it
    3. Runs Vision Analysis
    Returns a dict with paper info and analysis, or None
    """
    try:
        pmc_id = get_pmc_id(pmid)
        if not pmc_id:
            return None
        
        save_path = str(save_dir / f"{pmid}.pdf")

        if download_pdf(pmc_id, save_path):
            title = f"{topic} (ID: {pmid})"
            visual_analyses = []
            
            try:
                process_pdf(save_path, title)
                visual_analyses.append("Visual figures extracted and analyzed with AI vision.")
            except Exception as e:
                print(f"Error processing visuals {pmid}: {e}")
            
            try:
                ingest_full_text(save_path, pmid, title)
            except Exception as e:
                print(f"Error processing text {pmid}: {e}")
            
            return {
                "pmid": pmid,
                "title": title,
                "processed": True
            }
        else:
            return None
    except Exception as e:
        print(f"Error processing {pmid}: {e}")
        return None

@tool
def research_pubmed(topic: str) -> str:
    """
    Research a scientific topic using enhanced multi-source retrieval.
    1. Optimizes the search query for better results
    2. Searches PubMed and Semantic Scholar
    3. Ranks papers by semantic relevance
    4. Filters to the most relevant papers using AI
    5. Returns the paper content for context.

    Use this tool when the user asks about a topic you don't have context for.
    """
    import json
    from app.enhanced_retrieval import enhanced_retrieval
    from app.ingestion import ingest_paper_batch
    
    # Use enhanced retrieval to get relevant papers
    papers = enhanced_retrieval(topic, max_final_papers=8)
    
    if not papers:
        return f"I searched multiple scientific databases for '{topic}' but found no relevant papers."
    
    # Convert to format expected by ingest_paper_batch
    papers_for_ingest = []
    for paper in papers:
        papers_for_ingest.append({
            "title": paper['title'],
            "abstract": paper['abstract'],
            "journal": paper.get('journal', ''),
            "year": paper.get('year', 0),
            "source_id": paper.get('pmid', '')
        })
    
    # Ingest papers into Weaviate for RAG
    ingest_paper_batch(papers_for_ingest)
    
    result_parts = [f"Found and analyzed {len(papers)} relevant papers about '{topic}':\n"]
    sources = []
    
    for i, paper in enumerate(papers, 1):
        result_parts.append(f"\n--- Paper {i} ---")
        result_parts.append(f"Title: {paper['title']}")
        result_parts.append(f"Journal: {paper.get('journal', 'N/A')} ({paper.get('year', 'N/A')})")
        result_parts.append(f"PMID: {paper.get('pmid', 'N/A')}")
        result_parts.append(f"Citations: {paper.get('citation_count', 0)}")
        if paper.get('relevance_reason'):
            result_parts.append(f"Relevance: {paper['relevance_reason']}")
        abstract = paper['abstract']
        if len(abstract) > 1500:
            abstract = abstract[:1500] + "..."
        result_parts.append(f"Abstract: {abstract}")
        
        sources.append({
            "index": i,
            "title": paper['title'],
            "journal": paper.get('journal', ''),
            "year": paper.get('year', 0),
            "pmid": paper.get('pmid', ''),
            "abstract": paper['abstract'][:500] + "..." if len(paper['abstract']) > 500 else paper['abstract'],
            "url": paper.get('url', f"https://pubmed.ncbi.nlm.nih.gov/{paper.get('pmid', '')}/")
        })
    
    sources_json = json.dumps(sources).replace("{", "{{").replace("}", "}}")
    result_parts.append(f"\n\n[SOURCES_JSON]{sources_json}[/SOURCES_JSON]")
    
    return "\n".join(result_parts)

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

    result_parts = [f"Processed {len(processed_results)} papers with visual analysis:\n"]
    
    for paper in processed_results:
        result_parts.append(f"\n--- Paper: {paper['title']} ---")
        result_parts.append(f"PMID: {paper['pmid']}")
        result_parts.append("Visual figures have been extracted and analyzed with AI vision. The analysis has been stored for context.")
    
    return "\n".join(result_parts)