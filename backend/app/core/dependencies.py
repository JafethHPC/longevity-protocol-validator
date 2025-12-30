"""
FastAPI Dependencies

FastAPI dependency injection for services and configuration.
Using Depends() pattern makes testing easier and follows FastAPI best practices.
"""
from functools import lru_cache
from typing import Generator

from app.core.config import Settings
from app.services.cache import ReportCache


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.
    
    Uses lru_cache to ensure settings are only loaded once.
    Can be overridden in tests using app.dependency_overrides.
    
    Example test override:
        def get_settings_override():
            return Settings(openai_api_key=SecretStr("test-key"))
        
        app.dependency_overrides[get_settings] = get_settings_override
    """
    return Settings()


@lru_cache()
def get_cache() -> ReportCache:
    """
    Get the report cache instance.
    
    Uses lru_cache to ensure only one cache instance is created.
    Can be overridden in tests to use a mock cache.
    
    Example test override:
        class MockCache:
            def get(self, report_id): return None
            def set(self, report): pass
            
        app.dependency_overrides[get_cache] = lambda: MockCache()
    """
    return ReportCache()


# Future dependencies can be added here:
# - get_llm() for LLM client injection
# - get_embeddings() for embedding client injection
# - get_database() for database connections
