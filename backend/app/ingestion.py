import os
import weaviate
import weaviate.classes.config as wvc
from Bio import Entrez
from app.core.config import settings
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

TEST_PUBMED_ID = "19587680"

def fetch_paper_details(pubmed_id):
    """
    Fetches the title and abstract of a paper from PubMed
    """
    Entrez.email = "your_email@example.com"

    print(f"Fetching paper details for {pubmed_id}")

    try:
        handle = Entrez.efetch(db="pubmed", id=pubmed_id, retmode="xml")
        records = Entrez.read(handle)
        handle.close()

        paper = records['PubmedArticle'][0]
        article = paper['MedlineCitation']['Article']

        abstract_list = article.get('Abstract', {}).get('AbstractText', [])
        abstract = " ".join(abstract_list) if abstract_list else "No Abstract Found."

        try:
            year = article['Journal']['JournalIssue']['PubDate'].get('Year')
        except (ValueError, TypeError):
            year = None

        return {
            "title": article['ArticleTitle'],
            "abstract": abstract,
            "journal": article['Journal'].get('Title', article['Journal'].get('ISOAbbreviation', 'N/A')),
            "year": year,
            "source_id": pubmed_id
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return None

def ingest_paper(paper_data):
    """
    Connects to Weaviate and stores the paper data
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
                vector_config=wvc.Configure.Vectorizer.text2vec_openai(),
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

        uuid = papers_collection.data.insert(
            properties=paper_data
        )
        print(f"Stored paper in Weaviate. UUID: {uuid}")

    finally:
        client.close()

if __name__ == "__main__":
    data = fetch_paper_details(TEST_PUBMED_ID)
    
    if data and data['abstract'] != "No Abstract Found.":
        ingest_paper(data)
    else:
        print("Skipped ingestions: Invalid data")