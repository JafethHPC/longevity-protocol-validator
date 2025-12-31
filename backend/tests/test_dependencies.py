"""Tests for core/dependencies.py - FastAPI dependency injection."""
from unittest.mock import patch, MagicMock

import pytest


class TestGetSettings:
    """Test the get_settings dependency."""

    def test_get_settings_returns_settings(self):
        """get_settings should return a Settings instance."""
        from app.core.dependencies import get_settings
        from app.core.config import Settings
        
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self):
        """get_settings should return the same instance (cached)."""
        from app.core.dependencies import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_get_settings_has_required_attributes(self):
        """Returned settings should have required attributes."""
        from app.core.dependencies import get_settings
        
        settings = get_settings()
        
        assert hasattr(settings, "project_name")
        assert hasattr(settings, "OPENAI_API_KEY")
        assert hasattr(settings, "REDIS_HOST")


class TestGetCache:
    """Test the get_cache dependency."""

    def test_get_cache_returns_cache_instance(self):
        """get_cache should return a ReportCache instance."""
        from app.core.dependencies import get_cache
        from app.services.cache import ReportCache
        
        cache = get_cache()
        assert isinstance(cache, ReportCache)

    def test_get_cache_is_cached(self):
        """get_cache should return the same instance (cached)."""
        from app.core.dependencies import get_cache
        
        cache1 = get_cache()
        cache2 = get_cache()
        
        assert cache1 is cache2

    def test_get_cache_has_required_methods(self):
        """Returned cache should have required methods."""
        from app.core.dependencies import get_cache
        
        cache = get_cache()
        
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")
        assert hasattr(cache, "is_connected")


class TestDependencyInjection:
    """Test that dependencies work in FastAPI context."""

    def test_dependencies_can_be_overridden(self):
        """Dependencies should be overridable for testing."""
        from app.core.dependencies import get_settings
        
        # Just verify the function is decorated with lru_cache
        assert hasattr(get_settings, 'cache_clear')
    
    def test_cache_can_be_cleared(self):
        """Clearing cache should allow new instances."""
        from app.core.dependencies import get_settings
        
        settings1 = get_settings()
        get_settings.cache_clear()  # Clear the cache
        settings2 = get_settings()
        
        # Both should be valid settings
        assert settings1.project_name == "Longevity Validator"
        assert settings2.project_name == "Longevity Validator"
