import weaviate
import weaviate.classes.query as wvq
from app.core.config import settings

def search_papers(query_text: str):
    """
    Connects to Weaviate and retrieves papers based on the query text
    """
    client = weaviate.connect_to_local(
        headers={
            "X-OpenAI-Api-Key": settings.OPENAI_API_KEY
        }
    )

    try:
        papers = client.collections.get("Paper")

        response = papers.query.near_text(
            query=query_text,
            limit=2,
            return_metadata=wvq.MetadataQuery(distance=True)
        )

        print(query_text)
        
        for obj in response.objects:
            print(f"Title: {obj.properties['title']}")
            print(f"Distance: {obj.metadata.distance:.4f}")
            print(f"Abstract: {obj.properties['abstract'][:50]}")

    finally:
        client.close()

if __name__ == "__main__":
    search_papers("What compounds extend lifespan in mammals?")