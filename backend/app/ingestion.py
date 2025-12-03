import os
import weaviate
import weaviate.classes.config as wvc
from Bio import Entrez
from app.core.config import settings
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

Entrez.email = "your_email@example.com"

def search_pubmed_ids(term: str, max_results: int = 10) -> list[str]:
    """
    Searches for PubMed IDs based on a search term
    """
    try:
        handle = Entrez.esearch(db="pubmed", term=term, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        print(record)
        ids = record["IdList"]
        return ids
    except Exception as e:
        print(f"Error searching PubMed: {e}")
        return []

def fetch_details_batch(id_list: list[str]):
    """
    Fetches batch of paper details from PubMed
    """
    if not id_list:
        return []

    print(len(id_list))
    ids_str = ",".join(id_list)

    try:
        handle = Entrez.efetch(db="pubmed", id=ids_str, retmode="xml")
        records = Entrez.read(handle)
        handle.close()

        cleaned_papers = []
        pubmed_articles = records['PubmedArticle']

        for paper in pubmed_articles:
            try:
                article = paper['MedlineCitation']['Article']
                
                abstract_list = article.get('Abstract', {}).get('AbstractText', [])
                abstract_text = " ".join(abstract_list) if abstract_list else "No Abstract Found."

                if abstract_text == "No Abstract Found.":
                    continue

                cleaned_papers.append({
                    "title": article['ArticleTitle'],
                    "abstract": abstract_text,
                    "journal": article['Journal']['Title'],
                    "year": int(article['Journal']['JournalIssue']['PubDate'].get('Year', 0)),
                    "source_id": paper['MedlineCitation']['PMID']
                })
            except KeyError:
                continue

        return cleaned_papers
    except Exception as e:
        print(f"Error fetching details: {e}")
        return []

def ingest_paper_batch(paper_data: list[dict]):
    """
    Connects to Weaviate and does a bulk ingestion of the paper data
    """
    client = weaviate.connect_to_local(
        headers={
            "X-OpenAI-Api-Key": settings.OPENAI_API_KEY
        }
    )

    try:
        if not client.collections.exists("Paper"):
            client.collections.create(
                name="Paper",
                vectorizer_config=wvc.Configure.Vectorizer.text2vec_openai(),
                properties=[
                    wvc.Property(name="title", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="abstract", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="journal", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="year", data_type=wvc.DataType.INT),
                    wvc.Property(name="source_id", data_type=wvc.DataType.TEXT)
                ]
            )
            print("Create Schema")
        
        papers_collection = client.collections.get("Paper")

        with papers_collection.batch.dynamic() as batch:
            for paper in paper_data:
                batch.add_object(
                    properties=paper
                )
        
        print(f"Ingestion of {len(paper_data)} papers completed")

    finally:
        client.close()

if __name__ == "__main__":
    SEARCH_TERM = "longevity AND (rapamycin OR metformin OR fasting)"

    ids = search_pubmed_ids(SEARCH_TERM)

    papers = fetch_details_batch(ids)

    if papers:
        ingest_paper_batch(papers)
    else:
        print("No papers found")