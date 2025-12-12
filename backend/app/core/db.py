import weaviate
import os
from app.core.config import settings

def get_weaviate_client():
    """
    Returns a connected Weaviate client.
    Prioritizes Cloud URL if it exists in settings
    """
    if settings.WEAVIATE_URL:
        return weaviate.connect_to_weaviate_cloud(
            cluster_url=settings.WEAVIATE_URL,
            auth_credentials=weaviate.auth.AuthApiKey(settings.WEAVIATE_API_KEY),
            headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY}
        )
    else:
        return weaviate.connect_to_local(
            headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY}
        )