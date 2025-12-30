"""
LLM Client Management

Provides cached instances of LLM clients to avoid recreating
connections for every call. Uses lru_cache for thread-safe
singleton-like behavior.
"""
from functools import lru_cache
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings


# Cache multiple model configurations (mini and full gpt-4o)
@lru_cache(maxsize=4)
def get_llm(
    model: str = "gpt-4o-mini",
    temperature: float = 0.0
) -> ChatOpenAI:
    """
    Get a cached LLM instance.
    
    Uses lru_cache to ensure the same instance is reused across calls.
    This is more efficient than creating a new client for each request.
    
    Args:
        model: OpenAI model name (e.g., "gpt-4o-mini", "gpt-4o")
        temperature: Temperature for generation (0 = deterministic)
        
    Returns:
        Cached ChatOpenAI instance
    """
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.OPENAI_API_KEY
    )


@lru_cache(maxsize=2)
def get_embeddings(model: str = "text-embedding-3-small") -> OpenAIEmbeddings:
    """
    Get a cached embeddings instance.
    
    Uses lru_cache to ensure the same instance is reused across calls.
    
    Args:
        model: OpenAI embedding model name
        
    Returns:
        Cached OpenAIEmbeddings instance
    """
    return OpenAIEmbeddings(
        model=model,
        api_key=settings.OPENAI_API_KEY
    )


def get_structured_llm(output_schema):
    """
    Get an LLM configured for structured output.
    
    This creates a new instance each time because with_structured_output
    returns a new object. The underlying HTTP client is still shared.
    
    Args:
        output_schema: Pydantic model or schema for output structure
        
    Returns:
        LLM configured for structured output
    """
    return get_llm().with_structured_output(output_schema)


def clear_llm_cache():
    """
    Clear the LLM client cache.
    
    Useful for testing or when you need to force re-initialization.
    """
    get_llm.cache_clear()
    get_embeddings.cache_clear()
